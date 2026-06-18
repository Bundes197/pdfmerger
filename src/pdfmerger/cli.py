from pypdf import PdfWriter
from argparse import ArgumentParser, Namespace, Action
from pathlib import Path
import logging
import time
import sys
import os

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
                            description="A command line tool to merge pdfs into one file.",
                            suggest_on_error=True)
    
    parser.add_argument('-o', '--output', default='output.pdf', help='Name of merged output file')
    parser.add_argument('-f', '--force', action='store_true', help='Overwrite output file if it already exists')
    parser.add_argument('-P', '--password', help='Encrypt the output PDF with a password')

    parser.add_argument('-d', '--dir', action=InputAction, help='Search directory for PDF files')
    parser.add_argument('-r', '--recursive', action='store_true', help='Search directory recursively (requires -d)')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-S', '--sort', action='store_true', help='Sort searched PDF files (requires -d)')
    group.add_argument('-R', '--reverse', action='store_true', help='Reverse sort searched PDF files (requires -d)')

    parser.add_argument('-p', '--pages', nargs='+', help='Specify page ranges to extract (e.g., 1-3 5 7-end). Applies to all inputs.')
    parser.add_argument('-c', '--compress', action='store_true', help='Compress and optimize the size of the output PDF')
    parser.add_argument('--add-bookmarks', action='store_true', help='Add bookmarks using input filenames for easier navigation')
    parser.add_argument('--clear-metadata', action='store_true', help='Remove all metadata from the output PDF for anonymization')
    

    parser.add_argument('-l', '--log', action='store_true', help='Create output log')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1.0', help='Print version of pdfmerger')
    parser.add_argument('--verbose', action='store_true', help='Provides a verbose description')

    parser.add_argument('files', nargs='*', action=InputAction, help='Input files to merge')

    return parser

def check_arguments(arguments: Namespace) -> None:
    if arguments.log:
        timestr = time.strftime("%Y%m%d-%H%M%S")
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_path = log_dir / f"log-{timestr}.log"

        log_handlers = [logging.FileHandler(log_path)]

        if arguments.verbose:
            log_handlers.append(logging.StreamHandler(sys.stdout))

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=log_handlers
        )

        logging.info("Log file initialization successful.")
    else:
        # If verbose, print everything into the terminal, if not, print only warnings and critical errors
        if arguments.verbose:
            logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)s: %(message)s")
        else:
            logging.basicConfig(level=logging.WARNING, stream=sys.stdout, format="%(levelname)s: %(message)s")
    
    if not getattr(arguments, 'files', None) and not getattr(arguments, 'dir', None):
        msg: str = "You must provide either input files or a search directory (-d)."
        logging.critical("check_arguments(): %s", msg)
        sys.exit(f"pdfmerger: {msg}")
        
    if (arguments.recursive or arguments.sort or arguments.reverse) and not getattr(arguments, 'dir', None):
        msg: str = "Arguments -r, -S, and -R require a search directory (-d)."
        logging.critical("check_arguments(): %s", msg)
        sys.exit(f"pdfmerger: {msg}")

    if getattr(arguments, 'files', None):
        for file in getattr(arguments, 'files', []):
            path = Path(file)
            if not path.exists():
                msg: str = f"Input file '{file}' does not exist."
                logging.critical("check_arguments(): %s", msg)
                sys.exit(f"pdfmerger: {msg}")
            if not path.is_file():
                msg: str = f"'{file}' is not a valid file."
                logging.critical("check_arguments(): %s", msg)
                sys.exit(f"pdfmerger: {msg}")
            if path.suffix.lower() != '.pdf':
                msg: str = f"Input file '{file}' must be a PDF."
                logging.critical("check_arguments(): %s", msg)
                sys.exit(f"pdfmerger: {msg}")

    logging.info("check_arguments(): Input files are valid.")
    
    output_path = Path(arguments.output)
    if output_path.suffix.lower() != '.pdf':
        logging.info("check_arguments(): Output file name does not end with .pdf, adding pdf extension.")
        output_path = output_path.with_suffix('.pdf')
        arguments.output = str(output_path)

    logging.info("check_arguments(): Output file name is valid.")

    path = Path(arguments.output)
    if path.exists() and path.is_file() and not arguments.force:
        msg: str = f"File {path.stem} already exists, cannot overwrite file (use --force to force overwrite)."
        logging.critical("check_arguments(): %s", msg)
        sys.exit(f"pdfmerger: {msg}")
    
    logging.info("check_arguments(): Output file can be created.")
    logging.info("check_arguments(): Arguments are correct.")

def search_directory(path: Path, recursive: bool) -> list[str]:
    found_files: list[str] = []

    search_result: list[Path]
    if recursive:
        logging.info("search_directory(): Searching %s directory recursively.", path)
        search_result = list(path.rglob("*.pdf"))
    else:
        logging.info("search_directory(): Searching %s directory.", path)
        search_result = list(path.glob("*.pdf"))

    for file in search_result:
        found_files.append(str(file))

    return found_files

def get_all_files(arguments: Namespace) -> list[str]:
    all_files: list[str] = []

    if not hasattr(arguments, 'input_queue'):
        logging.info("get_all_files(): Input queue for files was not created, returning empty list.")
        return all_files
    
    input_type: str
    path: str
    for input_type, path in arguments.input_queue:
        if input_type == 'file':
            logging.info("get_all_files(): Adding %s to all files.", path)
            all_files.append(path)
        elif input_type == 'dir':
            dir_files: list[str] = []
            dir_files.extend(search_directory(Path(path), arguments.recursive))

            logging.info("get_all_files(): Found %d files in directory %s.", len(dir_files), path)
            
            if arguments.sort:
                logging.info("get_all_files(): Sorting files from %s directory.", path)
                dir_files.sort()
            elif arguments.reverse:
                logging.info("get_all_files(): Reverse sorting files from %s directory.", path)
                dir_files.sort(reverse=True)

            logging.info("get_all_files(): Adding files from directory %s to all files.", path)
            all_files.extend(dir_files)

    return all_files

def check_file_count(file_list: list[str]) -> None:
    if (len(file_list) < 2):
        msg: str = "You must provide at least 2 input files to merge."
        logging.critical("check_file_count(): %s", msg)
        sys.exit(f"pdfmerger: {msg}")

def merge_pdfs(merger: PdfWriter, arguments: Namespace, all_files: list[str]) -> None:
    logging.info("merge_pdfs(): merging all input PDF files.")
    for pdf in all_files:
        start_page = len(merger.pages)

        if arguments.pages:
            # Extracting pages
            pass
        else:
            merger.append(pdf)

        if arguments.add_bookmarks and len(merger.pages) != start_page:
            bookmark_title = Path(pdf).stem
            merger.add_outline_item(bookmark_title, page_number=start_page)
            logging.info("merge_pdfs(): added bookmark %s at page %d.", bookmark_title, start_page)

def main() -> None:
    parser = create_parser()

    arguments: Namespace = parser.parse_args()

    check_arguments(arguments)

    all_files: list[str] = get_all_files(arguments)
    check_file_count(all_files)

    merger = PdfWriter()

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

    merger.close()

if __name__ == "__main__":
    main()