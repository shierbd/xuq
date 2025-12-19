# MVP Phase Scripts

This directory contains the entry point scripts for each MVP phase.

## Scripts Structure

- `run_phase1_import.py` - Phase 1: Data import
- `run_phase2_clustering.py` - Phase 2: Large cluster generation
- `run_phase3_selection.py` - Phase 3: Cluster selection report generation
- `import_selection.py` - Phase 3b: Import manual selection results
- `run_phase4_demands.py` - Phase 4: Small clustering + demand card generation
- `run_incremental.py` - Phase 7: Incremental update

## Usage

All scripts should be run from the project root directory:

```bash
python scripts/run_phase1_import.py
```

## Implementation Status

- [x] Phase 1: Data import - COMPLETED (55,275 records imported)
- [ ] Phase 2: Large clustering - TODO
- [ ] Phase 3: Cluster selection - TODO
- [ ] Phase 4: Demand cards - TODO
- [ ] Phase 5: Tokens extraction - TODO (Optional)
- [ ] Phase 7: Incremental update - TODO (Optional)
