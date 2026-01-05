# What Test Files to Add

This guide tells you exactly what files to add and where.

## Quick Start

Add these 4 files to get started:

1. **`tests/test_data/text/sample.txt`** - Any text file (500+ words)
2. **`tests/test_data/markdown/sample.md`** - Any markdown file
3. **`tests/test_data/pdf/sample.pdf`** - Any PDF with extractable text (1-3 pages)
4. **`tests/test_data/docx/sample.docx`** - Any DOCX file (1-2 pages)

## Directory Structure

Files should be placed in:

```
tests/test_data/
├── text/
│   └── sample.txt          ← Add your text file here
├── markdown/
│   └── sample.md           ← Add your markdown file here
├── pdf/
│   └── sample.pdf          ← Add your PDF file here
└── docx/
    └── sample.docx         ← Add your DOCX file here
```

## File Requirements

### text/sample.txt

- **Format:** Plain text (UTF-8)
- **Size:** 500-1000 words
- **Content:** Multiple paragraphs
- **Purpose:** Basic text loading tests

### markdown/sample.md

- **Format:** Markdown (.md)
- **Content:** Headers, paragraphs, lists, links
- **Purpose:** Markdown loading tests

### pdf/sample.pdf

- **Format:** PDF with extractable text (not scanned images)
- **Pages:** 1-3 pages
- **Purpose:** PDF loading tests
- **Note:** Must have extractable text content

### docx/sample.docx

- **Format:** Microsoft Word DOCX
- **Pages:** 1-2 pages equivalent
- **Purpose:** DOCX loading tests

## Optional Files (For More Comprehensive Tests)

Once you have the minimum files, you can optionally add:

- `text/utf8_sample.txt` - Text with UTF-8 characters (emojis, special chars)
- `text/long_text.txt` - Longer text (2000+ words) for chunking tests
- `markdown/structured.md` - Markdown with code blocks and formatting
- `pdf/multi_page.pdf` - Multi-page PDF (5-10 pages)
- `docx/formatted.docx` - DOCX with formatting (headers, bold, lists)

## Example Content

You can find example content in:

- `tests/test_data/example_content/text_sample.txt` - Example text file
- `tests/test_data/example_content/markdown_sample.md` - Example markdown file

You can copy these to get started, or use your own files.

## How Tests Will Use These Files

Once you add the files:

1. **test_loaders.py** will test loading each file type
2. **test_ingestion_pipeline.py** will test the full ingestion pipeline
3. Tests will skip gracefully if files are missing (with warnings)
4. Tests will use actual files instead of temporary files

## Quick Check

After adding files, verify they exist:

```powershell
# Check files exist
ls tests/test_data/text/sample.txt
ls tests/test_data/markdown/sample.md
ls tests/test_data/pdf/sample.pdf
ls tests/test_data/docx/sample.docx
```

## Next Steps

1. Add the 4 minimum files listed above
2. Run tests: `python tests/test_loaders.py`
3. Tests will automatically detect and use your files
4. Add optional files for more comprehensive testing
