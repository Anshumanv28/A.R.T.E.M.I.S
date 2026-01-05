# Test Files Requirements

This document specifies what sample files you need to add for comprehensive testing.

## Location

All test files should be placed in: **`tests/test_data/`**

```
tests/test_data/
├── text/       # Text files (.txt)
├── markdown/   # Markdown files (.md)
├── pdf/        # PDF files (.pdf)
└── docx/       # DOCX files (.docx)
```

## Required Files

### Minimum Setup (Required for Tests to Pass)

1. **text/sample.txt** - Basic text file
2. **markdown/sample.md** - Basic markdown file
3. **pdf/sample.pdf** - PDF file with extractable text
4. **docx/sample.docx** - DOCX file

### Recommended Setup (For Full Test Coverage)

#### Text Files (`text/`)

- `sample.txt` - Basic text (500-1000 words, multiple paragraphs)
- `utf8_sample.txt` - Text with UTF-8 characters (emojis, special chars, non-ASCII)
- `long_text.txt` - Longer text (2000+ words, for chunking tests)

#### Markdown Files (`markdown/`)

- `sample.md` - Basic markdown (headers, paragraphs, lists, links)
- `structured.md` - Structured markdown (sections, nested headers, code blocks)

#### PDF Files (`pdf/`)

- `sample.pdf` - Basic PDF (1-3 pages, extractable text)
- `multi_page.pdf` - Multi-page PDF (5-10 pages)

#### DOCX Files (`docx/`)

- `sample.docx` - Basic DOCX (simple text content)
- `formatted.docx` - DOCX with formatting (headers, bold, italic, lists)

## File Specifications

### Text Files

**sample.txt:**

- Format: Plain text, UTF-8 encoding
- Size: 500-1000 words
- Content: Multiple paragraphs, various sentence structures
- Purpose: Basic text loading tests

**utf8_sample.txt:**

- Format: UTF-8 text with special characters
- Content: Emojis (🎉 ✅ ❌), accented characters (é ñ ü), non-Latin scripts (中文, العربية)
- Purpose: UTF-8 encoding tests

**long_text.txt:**

- Format: Plain text
- Size: 2000+ words
- Content: Multiple paragraphs, varied lengths
- Purpose: Chunking strategy tests

### Markdown Files

**sample.md:**

- Format: Standard markdown
- Content: Headers (# ## ###), paragraphs, lists, links, emphasis
- Purpose: Basic markdown loading

**structured.md:**

- Format: Structured markdown
- Content: Sections, nested headers, code blocks (```), tables
- Purpose: Complex markdown parsing tests

### PDF Files

**sample.pdf:**

- Format: PDF with extractable text (not scanned images)
- Pages: 1-3 pages
- Content: Text-based content
- Purpose: Basic PDF loading

**multi_page.pdf:**

- Format: Multi-page PDF
- Pages: 5-10 pages
- Content: Text across multiple pages
- Purpose: Page extraction and multi-page handling

### DOCX Files

**sample.docx:**

- Format: Microsoft Word DOCX
- Content: Plain text with simple formatting
- Pages: 1-2 pages equivalent
- Purpose: Basic DOCX loading

**formatted.docx:**

- Format: DOCX with formatting
- Content: Headers, bold, italic, lists, tables
- Purpose: Formatted content extraction

## Where to Get Sample Files

### Option 1: Create Your Own (Recommended)

Create simple files with sample content:

- Text: Use any text editor
- Markdown: Use any markdown editor or text editor
- PDF: Convert from text/markdown using pandoc or Word
- DOCX: Create in Word/LibreOffice or convert from markdown

### Option 2: Use Sample Content

Use provided sample content (see `tests/test_data/README.md` for examples)

### Option 3: Download Sample Files

Download small sample files from:

- Project documentation
- Public domain content
- Sample file repositories

**Important:** Ensure files don't contain sensitive or copyrighted content.

## Quick Creation Commands

### Using pandoc (if installed):

```bash
# Convert text to PDF
pandoc tests/test_data/text/sample.txt -o tests/test_data/pdf/sample.pdf

# Convert markdown to PDF
pandoc tests/test_data/markdown/sample.md -o tests/test_data/pdf/sample.pdf

# Convert markdown to DOCX
pandoc tests/test_data/markdown/sample.md -o tests/test_data/docx/sample.docx
```

### Using Python (python-docx):

```python
from docx import Document

# Create sample DOCX
doc = Document()
doc.add_heading('Sample Document', 0)
doc.add_paragraph('This is sample content for testing.')
doc.save('tests/test_data/docx/sample.docx')
```

## Verification

After adding files, verify structure:

```bash
# Check directory structure
ls -R tests/test_data/

# Should show:
# tests/test_data/text/
# tests/test_data/markdown/
# tests/test_data/pdf/
# tests/test_data/docx/
```

## Test Integration

Once files are added, tests will automatically:

- Detect files in `tests/test_data/`
- Use them for loader tests
- Use them for ingestion pipeline tests
- Skip gracefully if files are missing (with warnings)

## Notes

- Files are committed to repository (small sample files only)
- Use non-sensitive content
- Keep files reasonably small (<500KB each)
- Ensure PDFs have extractable text (not scanned images)
- Text files must use UTF-8 encoding
