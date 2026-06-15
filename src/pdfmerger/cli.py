from pypdf import PdfWriter
from argparse import ArgumentParser, Namespace
from pathlib import Path
import logging
import time
import sys

def main():
    parser = ArgumentParser(prog="pdfmerger",
                            description="A command line tool to merge pdfs into one file.",
                            suggest_on_error=True)
    
    parser.add_argument('files', nargs='*', help='Input files to merge')
    parser.add_argument('-o', default='output.pdf', help='Name of merged output file')
    parser.add_argument('-f', '--force', action='store_true', help='Overwrite output file if it already exists')

    parser.add_argument('-d', help='Search directory for pdf files')
    parser.add_argument('-r', action='store_true', help='Search directory recursively (requires -d)')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-S', action='store_true', help='Sort searched pdf files (requires -d)')
    group.add_argument('-R', action='store_true', help='Reverse sort searched pdf files (requires -d)')

    parser.add_argument('-p', '--pages', nargs='+', help='Specify page ranges to extract (e.g., 1-3 5 7-end). Applies to all inputs.')
    parser.add_argument('-P', '--password', help='Encrypt the output PDF with a password')

    parser.add_argument('-l', '--log', action='store_true', help='Create output log')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1.0', help='Print version of pdfmerger')
    parser.add_argument('--verbose', action='store_true', help='Provides a verbose description')

    arguments: Namespace = parser.parse_args()

    if arguments.log:
        timestr = time.strftime("%Y%m%d-%H%M%S")
        log_name = f"log-{timestr}.log"

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
        if arguments.verbose:
            logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)s: %(message)s")
        else:
            logging.basicConfig(level=logging.WARNING, stream=sys.stdout, format="%(levelname)s: %(message)s")
    
    if not arguments.files and not arguments.d:
        msg = "You must provide either input files or a search directory (-d)."
        logging.critical(msg)
        sys.exit(f"pdfmerger: {msg}")

    if arguments.files and len(arguments.files) < 2 and not arguments.d:
        msg = "You must provide at least 2 input files to merge."
        logging.critical(msg)
        sys.exit(f"pdfmerger: {msg}")
        
    if (arguments.r or arguments.S or arguments.R) and not arguments.d:
        msg = "Arguments -r, -S, and -R require a search directory (-d)."
        logging.critical(msg)
        sys.exit(f"pdfmerger: {msg}")


    if arguments.files:
        for file in arguments.files:
            path = Path(file)
            if not path.exists():
                msg = f"Input file '{file}' does not exist."
                logging.critical(msg)
                sys.exit(f"pdfmerger: {msg}")
            if not path.is_file():
                msg = f"'{file}' is not a valid file."
                logging.critical(msg)
                sys.exit(f"pdfmerger: {msg}")
            if path.suffix.lower() != '.pdf':
                msg = f"Input file '{file}' must be a PDF."
                logging.critical(msg)
                sys.exit(f"pdfmerger: {msg}")

    logging.info("Arguments are correct.")
    
    output_path = Path(arguments.o)
    if output_path.suffix.lower() != '.pdf':
        logging.info("Output file name does not end with .pdf, adding pdf extension")
        output_path = output_path.with_suffix('.pdf')
        arguments.o = str(output_path)

    logging.info("Output file name is valid.")

if __name__ == "__main__":
    main()