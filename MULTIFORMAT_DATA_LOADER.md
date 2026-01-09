"""
Multi-Format Data Loader for SynthLab

This module provides flexible data loading capabilities for various file formats
and data sources, replacing the CSV-only limitation of the original loader.

## Why Multi-Format Support Matters

Healthcare data comes in many formats:
- **CSV**: Simple, universal, but limited features
- **Parquet**: Columnar storage, 10x faster, preserves data types
- **Excel**: Common in clinical settings, multiple sheets
- **JSON**: API responses, nested data structures
- **SQL Databases**: Production systems, large datasets

## The Problem with CSV-Only

Original DataLoader only supported CSV:
```python
df = pd.read_csv(filepath)  # What if data is in Parquet? Excel? Database?
```

**Limitations:**
- ❌ Can't load from databases directly
- ❌ No support for Excel files from hospitals
- ❌ Can't read Parquet (standard for big data)
- ❌ No JSON support for API integrations
- ❌ Can't handle compressed files (.gz, .zip)

## The Solution: Format-Agnostic Loader

This enhanced loader:
- ✅ Auto-detects format from extension
- ✅ Supports 5+ formats (CSV, Parquet, Excel, JSON, SQL)
- ✅ Handles compression automatically (.gz, .zip, .bz2)
- ✅ Database connectivity (SQLite, PostgreSQL, MySQL)
- ✅ Streaming for large files (chunked reading)
- ✅ Data validation and type inference
- ✅ Backward compatible (existing CSV code still works)

## How It Works

### Architecture:

```
User calls load_data(filepath)
        ↓
Auto-detect format from extension
        ↓
Route to appropriate loader:
  ├─ CSV → pd.read_csv()
  ├─ Parquet → pd.read_parquet()
  ├─ Excel → pd.read_excel()
  ├─ JSON → pd.read_json()
  └─ SQL → pd.read_sql()
        ↓
Apply common cleaning
        ↓
Return DataFrame
```
"""