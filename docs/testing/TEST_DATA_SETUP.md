# Test Data Setup Guide

This guide helps you set up the test data files needed for comprehensive testing.

## Quick Start

1. Create the directory structure (already done if you see this file)
2. Add sample files to each subdirectory
3. Run the tests - they will use these files

## Directory Structure

```
tests/test_data/
├── text/          # Text files (.txt)
├── markdown/      # Markdown files (.md)
├── pdf/           # PDF files (.pdf)
└── docx/          # DOCX files (.docx)
```

## What Files to Add

### Minimum Required (for basic tests)

1. **text/sample.txt** - Any plain text file (500+ words)
2. **markdown/sample.md** - Any markdown file
3. **pdf/sample.pdf** - Any PDF with extractable text (1-3 pages)
4. **docx/sample.docx** - Any DOCX file (1-2 pages)

### Recommended (for comprehensive tests)

**Text Files:**

- `text/sample.txt` - Basic text
- `text/utf8_sample.txt` - Text with UTF-8 characters
- `text/long_text.txt` - Longer text (2000+ words)

**Markdown Files:**

- `markdown/sample.md` - Basic markdown
- `markdown/structured.md` - Markdown with sections/formatting

**PDF Files:**

- `pdf/sample.pdf` - Single or multi-page PDF
- `pdf/multi_page.pdf` - Multi-page PDF (5-10 pages)

**DOCX Files:**

- `docx/sample.docx` - Basic DOCX
- `docx/formatted.docx` - DOCX with formatting

## Quick File Creation

### Option 1: Use Sample Content (Recommended for Start)

Create minimal files to get started - you can expand later.

### Option 2: Use Real Documents

Use actual documents from your projects (make sure they're small and don't contain sensitive data).

### Option 3: Generate Programmatically

See [test_data_README.md](test_data_README.md) in this directory for code examples to generate files.

## File Naming Convention

- Use descriptive names: `sample.txt`, `utf8_sample.txt`, `long_text.txt`
- Use lowercase with underscores
- Keep names short but clear
- Match the pattern used in test files

## File Size Guidelines

- **Small files**: 1-50 KB (for fast tests)
- **Medium files**: 50-500 KB (for realistic tests)
- **Large files**: Avoid (>500 KB slows down tests)

## Content Guidelines

- Use non-sensitive content
- Include varied content (different languages, formats)
- Ensure files are well-formed (valid PDF, DOCX, etc.)
- Include edge cases (empty sections, special characters)

## Testing After Setup

Once you've added files, run:

```bash
# Test loaders
python tests/test_loaders.py

# Test ingestion pipeline
python tests/test_ingestion_pipeline.py

# Run all tests
pytest tests/ -v
```

Tests will automatically detect and use files in `tests/test_data/`.

## Troubleshooting

**Problem**: Tests fail with "File not found"

- **Solution**: Check that files exist in the correct subdirectories
- **Solution**: Verify file names match what tests expect

**Problem**: PDF/DOCX tests fail

- **Solution**: Ensure `pdfplumber`/`PyPDF2` is installed for PDFs
- **Solution**: Ensure `python-docx` is installed for DOCX
- **Solution**: Verify PDFs have extractable text (not just images)

**Problem**: Encoding errors with text files

- **Solution**: Ensure text files use UTF-8 encoding
- **Solution**: Check for invalid characters
