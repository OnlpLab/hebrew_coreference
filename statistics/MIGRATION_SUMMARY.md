# Statistics Folder Migration Summary

## 🎯 **Migration Completed Successfully**

All statistics scripts and their outputs have been moved to a dedicated `statistics/` folder for better organization.

## 📁 **New Structure**

```
statistics/
├── README.md                           # Documentation
├── run_all_statistics.py               # Master script to run all statistics
├── data_statistics.py                  # Basic dataset statistics
├── agreement_analysis.py               # Agreement analysis
├── comprehensive_statistics.py         # Combined statistics and visualization
├── tne_mention_statistics.py          # TNE mention characteristics
├── conllu_mention_counter.py          # CONLLU mention counting
├── final_statistics_summary.py        # Final summary report
└── outputs/                           # All output files
    ├── comprehensive_statistics.json   # Main statistics JSON
    ├── comprehensive_statistics.png    # Main visualization
    ├── agreement_analysis/            # Agreement analysis outputs
    ├── conllu_mention_analysis/       # CONLLU mention analysis
    ├── statistics/                    # Basic statistics outputs
    └── tne_mention_statistics/        # TNE mention analysis
```

## 🔧 **Path Updates Made**

### **Script Paths Updated:**
- All scripts now use `../data/corpus/...` to access data from the statistics folder
- Output paths updated to use relative paths within the statistics folder
- All scripts tested and working correctly

### **Files Moved:**
- **Scripts**: 6 statistics scripts moved from `scripts/` to `statistics/`
- **Outputs**: All output directories moved from `outputs/` to `statistics/outputs/`
- **Documentation**: README moved and updated with new paths

## 🚀 **Usage**

### **Run Individual Scripts:**
```bash
cd statistics
python data_statistics.py
python agreement_analysis.py
python comprehensive_statistics.py
python conllu_mention_counter.py
python final_statistics_summary.py
```

### **Run All Statistics:**
```bash
cd statistics
python run_all_statistics.py
```

## ✅ **Verification**

All scripts have been tested and work correctly from the new location:
- ✅ Paths updated correctly
- ✅ All outputs generated successfully
- ✅ No broken references
- ✅ Documentation updated

## 📊 **Key Statistics (Updated)**

- **Total Documents**: 351 (301 train, 26 dev, 24 test)
- **Total Mentions (no singleton)**: 19,483
- **Total Mentions (with singleton)**: 45,689
- **Singleton Mentions**: 26,206 (57.4%)
- **Average Mentions per Document**: 55.5 (no singleton), 130.2 (with singleton)

The statistics folder is now self-contained and organized for easy access and maintenance! 