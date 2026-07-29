import pytest
from pathlib import Path
from pypdf import PdfWriter, PdfReader
from pdfmerger.cli import (
    create_parser,
    check_arguments,
    parse_page_ranges,
    search_directory,
    get_all_files,
    merge_pdfs,
)

@pytest.fixture
def create_dummy_pdf(tmp_path):
    def _create(filename, num_pages=2):
        writer = PdfWriter()
        for _ in range(num_pages):
            writer.add_blank_page(width=100, height=100)
        
        file_path = tmp_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            writer.write(f)
        return file_path

    return _create


def test_parse_page_ranges_basic():
    total_pages = 10
    assert parse_page_ranges(["1-3"], total_pages) == [0, 1, 2]
    assert parse_page_ranges(["1", "end"], total_pages) == [0, 9]
    assert parse_page_ranges(["8-15"], total_pages) == [7, 8, 9]

def test_parse_page_ranges_edge_cases():
    total_pages = 5
    assert parse_page_ranges(["3"], total_pages) == [2]
    assert parse_page_ranges(["-2"], total_pages) == [0, 1]
    assert parse_page_ranges(["4-"], total_pages) == [3, 4]



def test_check_arguments_no_inputs():
    parser = create_parser()
    args = parser.parse_args([])

    with pytest.raises(SystemExit) as exc_info:
        check_arguments(args)
    assert exc_info.value.code == 1

def test_check_arguments_recursive_without_dir(create_dummy_pdf):
    in_file = create_dummy_pdf("test.pdf")
    parser = create_parser()
    args = parser.parse_args(["-r", str(in_file)])

    with pytest.raises(SystemExit) as exc_info:
        check_arguments(args)
    assert exc_info.value.code == 1

def test_check_arguments_nonexistent_file(tmp_path):
    parser = create_parser()
    args = parser.parse_args([str(tmp_path / "nonexistent.pdf")])

    with pytest.raises(SystemExit) as exc_info:
        check_arguments(args)
    assert exc_info.value.code == 1

def test_check_arguments_non_pdf_file(tmp_path):
    txt_file = tmp_path / "document.txt"
    txt_file.write_text("content")

    parser = create_parser()
    args = parser.parse_args([str(txt_file)])

    with pytest.raises(SystemExit) as exc_info:
        check_arguments(args)
    assert exc_info.value.code == 1

def test_check_arguments_adds_pdf_extension(create_dummy_pdf):
    in_file = create_dummy_pdf("input.pdf")
    parser = create_parser()
    args = parser.parse_args(["-o", "my_output_pdf", str(in_file)])

    check_arguments(args)
    assert args.output == "my_output_pdf.pdf"

def test_missing_force_flag_fails(create_dummy_pdf):
    out_file = create_dummy_pdf("output.pdf", 1)
    in_file = create_dummy_pdf("input.pdf", 1)

    parser = create_parser()
    args = parser.parse_args(["-o", str(out_file), str(in_file)])

    with pytest.raises(SystemExit) as exc_info:
        check_arguments(args)
    assert exc_info.value.code == 1

def test_force_flag_succeeds(create_dummy_pdf):
    out_file = create_dummy_pdf("output.pdf", 1)
    in_file = create_dummy_pdf("input.pdf", 1)

    parser = create_parser()
    args = parser.parse_args(["-f", "-o", str(out_file), str(in_file)])

    check_arguments(args)



def test_search_directory_recursive(tmp_path, create_dummy_pdf):
    create_dummy_pdf("top.pdf")
    create_dummy_pdf("subdir/nested.pdf")

    flat_results = search_directory(tmp_path, recursive=False)
    assert len(flat_results) == 1

    recursive_results = search_directory(tmp_path, recursive=True)
    assert len(recursive_results) == 2

def test_get_all_files_sorting(tmp_path, create_dummy_pdf):
    create_dummy_pdf("b.pdf")
    create_dummy_pdf("a.pdf")

    parser = create_parser()

    args_sort = parser.parse_args(["-d", str(tmp_path), "-S"])
    files_sorted = get_all_files(args_sort)
    assert Path(files_sorted[0]).name == "a.pdf"
    assert Path(files_sorted[1]).name == "b.pdf"

    args_rev = parser.parse_args(["-d", str(tmp_path), "-R"])
    files_rev = get_all_files(args_rev)
    assert Path(files_rev[0]).name == "b.pdf"
    assert Path(files_rev[1]).name == "a.pdf"



def test_merge_pdfs_full_flow(create_dummy_pdf, tmp_path):
    pdf1 = create_dummy_pdf("doc1.pdf", num_pages=2)
    pdf2 = create_dummy_pdf("doc2.pdf", num_pages=3)
    out_file = tmp_path / "merged_result.pdf"

    parser = create_parser()
    args = parser.parse_args(["-o", str(out_file), str(pdf1), str(pdf2)])

    merger = PdfWriter()
    all_files = [str(pdf1), str(pdf2)]
    merge_pdfs(merger, args, all_files)
    
    with open(out_file, "wb") as f:
        merger.write(f)
    merger.close()

    reader = PdfReader(out_file)
    assert len(reader.pages) == 5


def test_merge_pdfs_with_page_extraction(create_dummy_pdf, tmp_path):
    pdf1 = create_dummy_pdf("doc1.pdf", num_pages=5)
    out_file = tmp_path / "extracted.pdf"

    parser = create_parser()
    args = parser.parse_args(["-o", str(out_file), "-p", "1-2", str(pdf1)])

    merger = PdfWriter()
    merge_pdfs(merger, args, [str(pdf1)])
    
    with open(out_file, "wb") as f:
        merger.write(f)
    merger.close()

    reader = PdfReader(out_file)
    assert len(reader.pages) == 2