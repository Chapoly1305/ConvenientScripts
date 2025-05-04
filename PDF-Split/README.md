# PDF Splitter

Adobe Acrobat Reader Pro is too expensive for splitting PDFs, and the free version doesn't support splitting by
bookmarks. This script is a simple solution to split PDFs based on their bookmark structure.
A Python utility for splitting PDF documents according to bookmark structure, organizing chapters and sections into a
clean hierarchical folder structure.

## Purpose

This tool automatically splits a PDF document based on its bookmarks, creating a folder structure that mirrors the
document's organization. It's especially useful for:

- Breaking large technical documents into manageable pieces
- Organizing reference materials by chapter and section
- Creating a navigable file structure from PDFs with complex hierarchies
- Extracting specific chapters or sections from lengthy documents

## Requirements

- Python 3.6 or higher
- PyPDF2 library

```bash
pip install PyPDF2
```

## Basic Usage

```bash
python pdf_split.py your_document.pdf
```

This will:

1. Create a root folder named after your PDF file
2. Create subfolders for each chapter (including chapter names)
3. Split the PDF into section files placed in their respective chapter folders

## Command-line Options

```
python pdf_split.py [OPTIONS] input_pdf

Options:
  -o, --output-dir     Specify output directory (default: same as input)
  --min-level          Minimum section level to extract (default: 1)
  --max-level          Maximum section level to extract (default: 1)
```

## Example Output

When running the script on a technical specification document like "Matter-1.4-Core-Specification.pdf", you'll get a
folder structure like:

```
Matter-1.4-Core-Specification/
├── Chapter_1_Introduction/
│   ├── 1_1_Overview.pdf
│   ├── 1_2_References.pdf
│   ├── 1_3_Terminology.pdf
│   └── 1_4_Conventions.pdf
├── Chapter_2_Architecture/
│   ├── 2_1_Overview.pdf
│   ├── 2_2_Building_Blocks.pdf
│   ├── 2_3_System_Topology.pdf
│   └── 2_4_Security.pdf
├── Chapter_11_Service_and_Device_Management/
│   ├── 11_1_Basic_Information_Cluster.pdf
│   ├── 11_19_Administrator_Commissioning_Cluster.pdf
│   ├── 11_20_Over-the-Air_OTA_Software_Update.pdf
│   └── 11_21_Over-the-Air_OTA_Software_Update_File_Format.pdf
└── ...
```

## Customization Options

### Different Section Levels

By default, the script splits by first-level sections (e.g., "1.1", "1.2"). To split by different levels:

```bash
# Split by chapter level sections (e.g., "1", "2")
python pdf_split.py your_document.pdf --min-level 0 --max-level 0

# Split by subsections (e.g., "1.1.1", "1.1.2")
python pdf_split.py your_document.pdf --min-level 2 --max-level 2

# Split by both sections and subsections
python pdf_split.py your_document.pdf --min-level 1 --max-level 2
```

## Troubleshooting

If the script doesn't find sections at the expected level:

1. The script will show sample bookmarks from your PDF. Check that they match the expected format.
2. Try adjusting the `--min-level` and `--max-level` parameters to match your document's structure.
3. For PDFs with unusual bookmark structures, the script will attempt to identify chapters and use them as sections.

## Known Limitations

- Works best with PDFs that have structured bookmarks
- Some PDFs may have visual bookmarks that aren't properly encoded in the PDF structure
- Very large PDFs may require additional memory

## License

MIT License - Feel free to modify and distribute as needed.