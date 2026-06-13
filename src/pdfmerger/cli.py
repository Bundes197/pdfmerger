from pypdf import PdfWriter
from argparse import ArgumentParser, Namespace
from pathlib import Path

def main():
    parser = ArgumentParser(prog="pdfmerger",
                                    description="A command line tool to merge pdfs into one file.",
                                    suggest_on_error=True)
    
    parser.add_argument('files', nargs='+', help='Input files to merge')
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

    parser

    arguments: Namespace = parser.parse_args()
    
    if not arguments.files and not arguments.d:
        parser.error("You must provide either input files or a search directory (-d).")

    if arguments.filenfilesame and len(arguments.filename) < 2:
        parser.error("You must provide at least 2 input files to merge.")
        
    if (arguments.r or arguments.S or arguments.R) and not arguments.d:
        parser.error("Arguments -r, -S, and -R require a search directory (-d).")

    if arguments.files:
        for file in arguments.files:
            path = Path(file)
            if not path.exists():
                parser.error(f"Input file '{file}' does not exist.")
            if not path.is_file():
                parser.error(f"'{file}' is not a valid file.")
            if path.suffix.lower() != '.pdf':
                parser.error(f"Input file '{file}' must be a PDF.")
    
    output_path = Path(arguments.o)
    if output_path.suffix.lower() != '.pdf':
        output_path = output_path.with_suffix('.pdf')
        arguments.o = str(output_path)

    print(arguments)


if __name__ == "__main__":
    main()