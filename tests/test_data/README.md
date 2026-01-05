# Test Data Directory

This directory contains sample files used for testing file loaders and ingestion pipelines.

## Directory Structure

```
tests/test_data/
├── text/          # Text files (.txt)
├── markdown/      # Markdown files (.md)
├── pdf/           # PDF files (.pdf)
└── docx/          # DOCX files (.docx)
```

## Required Files

### Minimum Setup (Required for tests to run)

Add these files to enable tests:

1. **text/sample.txt** - Basic text file (500-1000 words)
2. **markdown/sample.md** - Basic markdown file
3. **pdf/sample.pdf** - PDF file with extractable text (1-3 pages)
4. **docx/sample.docx** - DOCX file (1-2 pages)

### Recommended Setup (For comprehensive testing)

#### Text Files (`text/`)

- `sample.txt` - Basic text (multiple paragraphs)
- `utf8_sample.txt` - Text with UTF-8 characters (emojis, special chars)
- `long_text.txt` - Longer text (2000+ words for chunking tests)

#### Markdown Files (`markdown/`)

- `sample.md` - Basic markdown (headers, lists, links)
- `structured.md` - Structured markdown (sections, code blocks)

#### PDF Files (`pdf/`)

- `sample.pdf` - Basic PDF (1-3 pages, extractable text)
- `multi_page.pdf` - Multi-page PDF (5-10 pages)

#### DOCX Files (`docx/`)

- `sample.docx` - Basic DOCX (simple text content)
- `formatted.docx` - DOCX with formatting (headers, bold, lists)

## File Specifications

See `TEST_FILES_REQUIREMENTS.md` in the `tests/` directory for detailed specifications.

## Example Content

See `example_content/` directory for example file content you can use as templates.

## Notes

- Files should be reasonably small (<500KB each)
- PDFs must have extractable text (not scanned images)
- Text files must use UTF-8 encoding
- Use non-sensitive content
- Files are committed to the repository (small sample files only)
