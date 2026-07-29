# pdfmerger
A command line tool to merge pdfs into one file.

`pdfmerger` is a light tool built with Python and `pypdf`. It allows you to merge multiple PDF files with directory scanning or given files, extract specific page ranges, encrypt output files, and manage PDF metadata.

---

## Features

* **Flexible Input:** Merge individual PDF files, entire directories, or both while preserving command-line argument order.
* **Directory Search:** Search for pdfs within directories with recursive scanning option and alphabetical sorting.
* **Page Selection:** Extract specific pages or ranges (e.g., `1-3, 5, 7-end`) across all inputs.
* **Security & Anonymization:** Encrypt output files using AES-256 and remove metadata.
* **Optimization & Navigation:** Compress output file size or automatically generate bookmarks based on input filenames.

---

## Installation

### Pre-built Binaries
Executables for Windows, macOS, and Linux are available under the **Releases** section of this repository.

### From Source
Clone the repository and install it using `pip`:

```bash
git clone https://github.com/your-username/pdfmerger.git
cd pdfmerger
pip3 install .
```

### Note for macOS users:
If macOS blocks the binary with a security warning, remove the quarantine attribute via Terminal in the directory where the executable is located:
```bash
xattr -d com.apple.quarantine pdfmerger
```

---

## Usage

```bash
pdfmerger [OPTIONS] [FILES...]
```

### Options

| Option | Short | Description |
| --- | --- | --- |
| `--output <file>` | `-o` | Name of merged output file (default: `output.pdf`). |
| `--force` | `-f` | Overwrite output file if it already exists. |
| `--dir <path>` | `-d` | Search directory for PDF files. |
| `--recursive` | `-r` | Search directory recursively (requires `-d`). |
| `--sort` | `-S` | Sort searched PDF files (requires `-d`). |
| `--reverse` | `-R` | Reverse sort searched PDF files (requires `-d`). |
| `--pages <spec>` | `-p` | Specify page ranges to extract (e.g., `1-3,5,7-end`). Applies to all inputs. |
| `--password <pass>` | `-P` | Encrypt the output PDF with a password. |
| `--compress` | `-c` | Compress and optimize the size of the output PDF. |
| `--add-bookmarks` | | Add bookmarks using input filenames for easier navigation. |
| `--clear-metadata` | | Remove all metadata from the output PDF for anonymization. |
| `--log` | `-l` | Create output log. |
| `--verbose` | | Provides a verbose description. |
| `--version` | `-v` | Print version of pdfmerger. |

---

## Page Range Syntax

The `-p` / `--pages` option accepts flexible page specifications. Page indexing starts at **1**, and the keyword `end` represents the final page of a document.

* `1-3`: Pages 1, 2, and 3.
* `5`: Page 5 only.
* `7-end`: Page 7 through the last page.
* `-3`: Pages 1 through 3.
* `5-`: Page 5 through the last page.
* `1-3,5,8-end`: Combination of multiple ranges separated by commas or spaces.

---

## Examples

**Basic Merge**
```bash
pdfmerger file1.pdf file2.pdf file3.pdf
```

**Specify Output File and Overwrite Existing**
```bash
pdfmerger -o merged.pdf -f file1.pdf file2.pdf
```

**Merge All PDFs in a Directory (Sorted Recursively)**
```bash
pdfmerger -d ./documents -r -S -o final_report.pdf
```

**Extract Specific Pages and Add Bookmarks**
```bash
pdfmerger -p "1-5, 10, 12-end" --add-bookmarks file1.pdf file2.pdf
```

**Encrypt, Compress, and Anonymize**
```bash
pdfmerger -P "Secret123" -c --clear-metadata -o secure.pdf file1.pdf file2.pdf
```

**Interleaved Files and Directories**
Preserves input order (processes `intro.pdf`, then sorted files from `./chapters`, then `conclusion.pdf`):
```bash
pdfmerger intro.pdf -d ./chapters -S conclusion.pdf -o complete_book.pdf
```

---

## Development & Testing

To run the test suite locally:

```bash
pip3 install pytest pypdf
pytest
```