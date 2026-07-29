from pypdf import PdfWriter, PdfReader
from argparse import ArgumentParser, Namespace, Action
from pathlib import Path
import logging
import time
import sys
import re

# For preserving order of the arguments
class InputAction(Action):
    def __call__(self,
                parser: ArgumentParser,
                namespace: Namespace,
                values: str | list[str] | None,
                option_string: str | None = None) -> None:
        if not hasattr(namespace, 'input_queue'):
            namespace.input_queue = []

        if option_string == '-d' or option_string == '--dir':
            namespace.input_queue.append(('dir', values))
            namespace.dir = values
            return
        elif option_string is None:
            if isinstance(values, list):
                for file in values:
                    namespace.input_queue.append(('file', file))
            else:
                namespace.input_queue.append(('file', values))
        
        # Updating self.dest (set automatically when calling InputAction) with new files
        current_files = getattr(namespace, self.dest) or []
        if isinstance(values, list):
            current_files.extend(values)
        else:
            current_files.append(values)
        setattr(namespace, self.dest, current_files)

def create_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="pdfmerger",
                            description="A command line tool to merge pdfs into one file.")
    
    parser.add_argument('-o', '--output', default='output.pdf', help='Name of merged output file')
    parser.add_argument('-f', '--force', action='store_true', help='Overwrite output file if it already exists')
    parser.add_argument('-P', '--password', help='Encrypt the output PDF with a password')

    parser.add_argument('-d', '--dir', action=InputAction, help='Search directory for PDF files')
    parser.add_argument('-r', '--recursive', action='store_true', help='Search directory recursively (requires -d)')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-S', '--sort', action='store_true', help='Sort searched PDF files (requires -d)')
    group.add_argument('-R', '--reverse', action='store_true', help='Reverse sort searched PDF files (requires -d)')

    parser.add_argument('-p', '--pages', type=str, help='Specify page ranges to extract (e.g., 1-3,5,7-end). Applies to all inputs.')
    parser.add_argument('-c', '--compress', action='store_true', help='Compress and optimize the size of the output PDF')
    parser.add_argument('--add-bookmarks', action='store_true', help='Add bookmarks using input filenames for easier navigation')
    parser.add_argument('--clear-metadata', action='store_true', help='Remove all metadata from the output PDF for anonymization')
    

    parser.add_argument('-l', '--log', action='store_true', help='Create output log')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1.0', help='Print version of pdfmerger')
    parser.add_argument('--verbose', action='store_true', help='Provides a verbose description')

    parser.add_argument('files', nargs='*', action=InputAction, help='Input files to merge')

    return parser

def check_arguments(arguments: Namespace) -> None:
    file_formatter: logging.Formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(funcName)s(): %(message)s")
    console_formatter: logging.Formatter = logging.Formatter("pdfmerger: %(levelname)s: %(message)s")
    handlers: list[logging.Handler] = []

    if arguments.log:
        timestr: str = time.strftime("%Y%m%d-%H%M%S")
        log_dir: Path = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_path: Path = log_dir / f"log-{timestr}.log"

        file_handler: logging.FileHandler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    console_handler: logging.StreamHandler = logging.StreamHandler(sys.stdout)
    if arguments.verbose:
        console_handler.setLevel(logging.INFO)
    else:
        console_handler.setLevel(logging.WARNING)
        
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    root_level: int
    if arguments.log or arguments.verbose:
        root_level = logging.INFO
    else:
        root_level = logging.WARNING

    logging.basicConfig(level=root_level, handlers=handlers)

    if arguments.log:
        logging.info("Log file initialization successful.")

    if getattr(arguments, 'pages', None):
        pattern = re.compile(r'^(\d+|end)?-?(\d+|end)?$')

        raw_pages = arguments.pages
        if isinstance(raw_pages, str):
            page_items = [p.strip() for p in raw_pages.replace(",", " ").split() if p.strip()]
        else:
            page_items = raw_pages

        for item in page_items:
            item_clean: str = item.lower().strip()

            if not item_clean or item_clean == '-':
                logging.critical("Invalid page range format: '%s'", item)
                sys.exit(1)

            if not pattern.match(item_clean):
                logging.critical("Invalid page range syntax: '%s'. Use numbers, ranges (e.g., 1-3) or 'end'.", item)
                sys.exit(1)

        logging.info("Page ranges syntax is valid.")
    
    if not getattr(arguments, 'files', None) and not getattr(arguments, 'dir', None):
        logging.critical("You must provide either input files or a search directory (-d).")
        sys.exit(1)
        
    if (arguments.recursive or arguments.sort or arguments.reverse) and not getattr(arguments, 'dir', None):
        logging.critical("Arguments -r, -S, and -R require a search directory (-d).")
        sys.exit(1)

    if getattr(arguments, 'files', None):
        for file in getattr(arguments, 'files', []):
            path: Path = Path(file)
            if not path.exists():
                logging.critical("Input file '%s' does not exist.", file)
                sys.exit(1)
            if not path.is_file():
                logging.critical("'%s' is not a valid file.", file)
                sys.exit(1)
            if path.suffix.lower() != '.pdf':
                logging.critical("Input file '%s' must be a PDF.", file)
                sys.exit(1)

    logging.info("Input files are valid.")
    
    output_path: Path = Path(arguments.output)
    if output_path.suffix.lower() != '.pdf':
        logging.info("Output file name does not end with .pdf, adding pdf extension.")
        output_path = output_path.with_suffix('.pdf')
        arguments.output = str(output_path)

    logging.info("Output file name is valid.")

    result_path: Path = Path(arguments.output)
    if result_path.exists() and result_path.is_file() and not arguments.force:
        logging.warning("File %s already exists, cannot overwrite file (use --force to force overwrite).", result_path.stem)
        sys.exit(1)
    
    logging.info("Output file can be created.")
    logging.info("Arguments are correct.")

def search_directory(path: Path, recursive: bool) -> list[str]:
    found_files: list[str] = []

    search_result: list[Path]
    if recursive:
        logging.info("Searching %s directory recursively.", path)
        search_result = list(path.rglob("*.pdf"))
    else:
        logging.info("Searching %s directory.", path)
        search_result = list(path.glob("*.pdf"))

    for file in search_result:
        found_files.append(str(file))

    return found_files

def get_all_files(arguments: Namespace) -> list[str]:
    all_files: list[str] = []

    if not hasattr(arguments, 'input_queue'):
        logging.info("Input queue for files was not created, returning empty list.")
        return all_files
    
    input_type: str
    path: str
    for input_type, path in arguments.input_queue:
        if input_type == 'file':
            logging.info("Adding %s to all files.", path)
            all_files.append(path)
        elif input_type == 'dir':
            dir_files: list[str] = []
            dir_files.extend(search_directory(Path(path), arguments.recursive))

            logging.info("Found %d files in directory %s.", len(dir_files), path)
            
            if arguments.sort:
                logging.info("Sorting files from %s directory.", path)
                dir_files.sort()
            elif arguments.reverse:
                logging.info("Reverse sorting files from %s directory.", path)
                dir_files.sort(reverse=True)

            logging.info("Adding files from directory %s to all files.", path)
            all_files.extend(dir_files)

    return all_files

def check_file_count(file_list: list[str]) -> None:
    if (len(file_list) < 1):
        logging.critical("You must provide at least 1 input file.")
        sys.exit(1)

def parse_page_ranges(pages_spec: str | list[str], total_pages: int) -> list[int]:
    indices: list[int] = []

    if isinstance(pages_spec, str):
        items = [p.strip() for p in pages_spec.replace(",", " ").split() if p.strip()]
    else:
        items = pages_spec

    for item in items:
        item: str = item.lower().strip()

        if '-' in item:
            start_str: str
            end_str: str
            start_str, end_str = item.split('-', 1)
            start_str = start_str.strip()
            end_str = end_str.strip()

            start: int
            if not start_str:
                start = 1
            elif start_str == 'end':
                start = total_pages
            else:
                start = int(start_str)

            end: int
            if not end_str:
                end = total_pages
            elif end_str == 'end':
                end = total_pages
            else:
                end = int(end_str)

            if start <= end:
                indices.extend(range(start - 1, end))
                
        else:
            if item == 'end':
                indices.append(total_pages - 1)
            else:
                indices.append(int(item) - 1)

    result: list[int] = []
    i: int
    for i in indices:
        if 0 <= i < total_pages:
            result.append(i)

    logging.info("Parsed user input into %d page indices.", len(result))
    return result

def merge_pdfs(merger: PdfWriter, arguments: Namespace, all_files: list[str]) -> None:
    logging.info("Merging all input PDF files.")
    for pdf in all_files:
        start_page: int = len(merger.pages)

        try:
            if arguments.pages:
                reader: PdfReader = PdfReader(pdf)
                total_pages: int = len(reader.pages)
                page_indices: list[int] = parse_page_ranges(arguments.pages, total_pages)
                
                idx: int
                for idx in page_indices:
                    merger.add_page(reader.pages[idx])

                logging.info("Extracted %d pages from %s", len(page_indices), pdf)
            else:
                merger.append(pdf)
                logging.info("Merged %s", pdf)
        except Exception as e:
            if "encrypt" in str(e).lower() or "password" in str(e).lower():
                logging.critical("Input file '%s' is encrypted and cannot be read.", pdf)
            else:
                logging.critical("Error processing file %s: %s", pdf, e)
            sys.exit(1)

        if arguments.add_bookmarks and len(merger.pages) != start_page:
            bookmark_title: str = Path(pdf).stem
            merger.add_outline_item(bookmark_title, page_number=start_page)
            logging.info("Added bookmark %s at page %d.", bookmark_title, start_page)

def main() -> None:
    parser: ArgumentParser = create_parser()

    arguments: Namespace = parser.parse_args()

    check_arguments(arguments)

    all_files: list[str] = get_all_files(arguments)
    check_file_count(all_files)

    merger: PdfWriter = PdfWriter()

    merge_pdfs(merger, arguments, all_files)

    if arguments.password:
        logging.info("Encrypting output PDF file with a password.")
        merger.encrypt(arguments.password, algorithm="AES-256")

    if arguments.clear_metadata:
        logging.info("Clearing output PDF file metadata.")
        merger.add_metadata({})

    if arguments.compress:
        logging.info("Compressing output PDF file.")
        merger.compress_identical_objects()

    merger.write(arguments.output)
    logging.info("Successfully created merged PDF at '%s'.", arguments.output)
    
    merger.close()

if __name__ == "__main__":
    main()