#!/bin/bash
# FE-EKG Codebase Cleanup Automation Script
# Usage: ./scripts/cleanup_automation.sh [phase]

set -e  # Exit on error

PROJECT_ROOT="/Users/hansonxiong/Desktop/DDP/feekg"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   FE-EKG Codebase Cleanup Automation                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}\n"

# Function to create backup
create_backup() {
    echo -e "${YELLOW}📦 Creating backup...${NC}"
    git checkout -b cleanup-backup-$(date +%Y%m%d-%H%M%S) 2>/dev/null || true
    git add -A
    git commit -m "Pre-cleanup backup $(date)" || echo "Nothing to commit"
    git checkout -b codebase-cleanup 2>/dev/null || git checkout codebase-cleanup
    echo -e "${GREEN}✅ Backup created${NC}\n"
}

# Phase 2.1: Consolidate Documentation
consolidate_docs() {
    echo -e "${YELLOW}📚 Phase 2.1: Consolidating documentation...${NC}\n"

    # Create docs directory
    mkdir -p docs

    # 1. AllegroGraph docs (3 → 1)
    echo "1️⃣  Consolidating AllegroGraph documentation..."
    if [ -f "ALLEGROGRAPH_COMPARISON.md" ]; then
        cat > docs/ALLEGROGRAPH_SETUP.md << 'EOF'
# AllegroGraph Setup Guide

This guide consolidates all AllegroGraph configuration and troubleshooting information.

---

## Quick Start

Use HTTPS connection on port 443:

```python
AG_URL=https://qa-agraph.nelumbium.ai:443/
AG_USER=<your-username>
AG_PASS=your_password
AG_REPO=feekg_dev
```

---

EOF
        cat ALLEGROGRAPH_COMPARISON.md >> docs/ALLEGROGRAPH_SETUP.md
        echo -e "\n---\n" >> docs/ALLEGROGRAPH_SETUP.md
        cat ALLEGROGRAPH_STATUS.md >> docs/ALLEGROGRAPH_SETUP.md
        echo -e "\n---\n" >> docs/ALLEGROGRAPH_SETUP.md
        cat ALLEGROGRAPH_NATIVE_CLIENT.md >> docs/ALLEGROGRAPH_SETUP.md

        # Add quick reference
        echo -e "\n---\n" >> docs/ALLEGROGRAPH_SETUP.md
        cat QUICK_REFERENCE_ALLEGROGRAPH.md >> docs/ALLEGROGRAPH_SETUP.md

        echo -e "   ${GREEN}✅ Created docs/ALLEGROGRAPH_SETUP.md${NC}"
    fi

    # 2. Lehman case study docs (2 → 1)
    echo "2️⃣  Consolidating Lehman case study docs..."
    if [ -f "LEHMAN_CASE_STUDY_PIPELINE.md" ]; then
        cat > docs/CASE_STUDY_LEHMAN.md << 'EOF'
# Lehman Brothers Case Study

Complete guide for the Lehman Brothers financial crisis case study.

---

EOF
        cat LEHMAN_CASE_STUDY_PIPELINE.md >> docs/CASE_STUDY_LEHMAN.md
        echo -e "\n---\n## Quick Start\n" >> docs/CASE_STUDY_LEHMAN.md
        cat QUICK_START_LEHMAN.md >> docs/CASE_STUDY_LEHMAN.md

        echo -e "   ${GREEN}✅ Created docs/CASE_STUDY_LEHMAN.md${NC}"
    fi

    # 3. Visualization docs (3 → 1)
    echo "3️⃣  Consolidating visualization docs..."
    if [ -f "VISUALIZATION_IMPROVEMENTS.md" ]; then
        cat > docs/VISUALIZATIONS.md << 'EOF'
# Visualization System

Complete guide to the FE-EKG visualization capabilities.

---

EOF
        cat VISUALIZATION_IMPROVEMENTS.md >> docs/VISUALIZATIONS.md
        echo -e "\n---\n## Timeline Visualization\n" >> docs/VISUALIZATIONS.md
        cat TIMELINE_VISUALIZATION.md >> docs/VISUALIZATIONS.md
        echo -e "\n---\n## Color Scheme\n" >> docs/VISUALIZATIONS.md
        cat COLOR_SCHEME.md >> docs/VISUALIZATIONS.md

        echo -e "   ${GREEN}✅ Created docs/VISUALIZATIONS.md${NC}"
    fi

    # 4. LLM/NLP docs (4 → 1)
    echo "4️⃣  Consolidating LLM/NLP docs..."
    if [ -f "LLM_INTEGRATION_SUMMARY.md" ]; then
        cat > docs/LLM_INTEGRATION.md << 'EOF'
# LLM and NLP Integration

Complete guide to AI-powered features in FE-EKG.

---

EOF
        cat LLM_INTEGRATION_SUMMARY.md >> docs/LLM_INTEGRATION.md
        echo -e "\n---\n## NLP Value Addition\n" >> docs/LLM_INTEGRATION.md
        cat NLP_VALUE_ADD.md >> docs/LLM_INTEGRATION.md
        echo -e "\n---\n## Classification Improvements\n" >> docs/LLM_INTEGRATION.md
        cat CLASSIFICATION_IMPROVEMENT.md >> docs/LLM_INTEGRATION.md
        echo -e "\n---\n## NVIDIA Quickstart\n" >> docs/LLM_INTEGRATION.md
        cat NVIDIA_QUICKSTART.md >> docs/LLM_INTEGRATION.md

        echo -e "   ${GREEN}✅ Created docs/LLM_INTEGRATION.md${NC}"
    fi

    # 5. Optimization docs (3 → 1)
    echo "5️⃣  Consolidating optimization docs..."
    if [ -f "OPTIMIZATION_REPORT.md" ]; then
        cat > docs/OPTIMIZATION.md << 'EOF'
# Performance Optimization

Complete guide to performance analysis and optimization strategies.

---

EOF
        cat OPTIMIZATION_REPORT.md >> docs/OPTIMIZATION.md
        echo -e "\n---\n## Pipeline Comparison\n" >> docs/OPTIMIZATION.md
        cat PIPELINE_COMPARISON.md >> docs/OPTIMIZATION.md
        echo -e "\n---\n## ETL Completion Summary\n" >> docs/OPTIMIZATION.md
        cat ETL_COMPLETION_SUMMARY.md >> docs/OPTIMIZATION.md

        echo -e "   ${GREEN}✅ Created docs/OPTIMIZATION.md${NC}"
    fi

    # 6. RDF docs (2 → 1)
    echo "6️⃣  Consolidating RDF docs..."
    if [ -f "RDF_CONVERSION_GUIDE.md" ]; then
        cat > docs/RDF_SETUP.md << 'EOF'
# RDF and Ontology Setup

Complete guide to RDF conversion and triple store configuration.

---

EOF
        cat RDF_CONVERSION_GUIDE.md >> docs/RDF_SETUP.md
        echo -e "\n---\n## RDF Database Options\n" >> docs/RDF_SETUP.md
        cat RDF_DATABASE_OPTIONS.md >> docs/RDF_SETUP.md

        echo -e "   ${GREEN}✅ Created docs/RDF_SETUP.md${NC}"
    fi

    # 7. Move core docs
    echo "7️⃣  Organizing core documentation..."
    [ -f "CLAUDE.md" ] && cp CLAUDE.md docs/PROJECT_GUIDE.md && echo -e "   ${GREEN}✅ Copied docs/PROJECT_GUIDE.md${NC}"
    [ -f "README.md" ] && cp README.md docs/README.md && echo -e "   ${GREEN}✅ Copied docs/README.md${NC}"

    # Create symlink for GitHub
    ln -sf docs/README.md README.md 2>/dev/null || true

    echo -e "\n${GREEN}✅ Phase 2.1 Complete!${NC}\n"
}

# Show what will be deleted
show_deletable_files() {
    echo -e "${YELLOW}🗑️  Files that can be safely deleted after consolidation:${NC}\n"

    echo "AllegroGraph docs:"
    ls -lh ALLEGROGRAPH_*.md QUICK_REFERENCE_ALLEGROGRAPH.md 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

    echo -e "\nLehman docs:"
    ls -lh LEHMAN_CASE_STUDY_PIPELINE.md QUICK_START_LEHMAN.md 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

    echo -e "\nVisualization docs:"
    ls -lh VISUALIZATION_IMPROVEMENTS.md TIMELINE_VISUALIZATION.md COLOR_SCHEME.md 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

    echo -e "\nLLM/NLP docs:"
    ls -lh LLM_INTEGRATION_SUMMARY.md NLP_VALUE_ADD.md CLASSIFICATION_IMPROVEMENT.md NVIDIA_QUICKSTART.md 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

    echo -e "\nOptimization docs:"
    ls -lh OPTIMIZATION_REPORT.md PIPELINE_COMPARISON.md ETL_COMPLETION_SUMMARY.md 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

    echo -e "\nRDF docs:"
    ls -lh RDF_CONVERSION_GUIDE.md RDF_DATABASE_OPTIONS.md 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

    echo -e "\n${YELLOW}Total size saved:${NC}"
    du -ch ALLEGROGRAPH_*.md LEHMAN_*.md VISUALIZATION_*.md TIMELINE_*.md COLOR_*.md \
        LLM_*.md NLP_*.md CLASSIFICATION_*.md NVIDIA_*.md \
        OPTIMIZATION_*.md PIPELINE_*.md ETL_*.md \
        RDF_*.md QUICK_*.md 2>/dev/null | tail -1
}

# Delete old files (after confirmation)
delete_old_files() {
    echo -e "${RED}⚠️  WARNING: This will DELETE old documentation files!${NC}"
    echo -e "${YELLOW}Make sure you've backed up and verified the new docs/ files.${NC}\n"

    read -p "Are you sure you want to delete old files? (yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        echo -e "\n${YELLOW}Deleting old files...${NC}"

        rm -f ALLEGROGRAPH_*.md QUICK_REFERENCE_ALLEGROGRAPH.md
        rm -f LEHMAN_CASE_STUDY_PIPELINE.md QUICK_START_LEHMAN.md
        rm -f VISUALIZATION_IMPROVEMENTS.md TIMELINE_VISUALIZATION.md COLOR_SCHEME.md
        rm -f LLM_INTEGRATION_SUMMARY.md NLP_VALUE_ADD.md CLASSIFICATION_IMPROVEMENT.md NVIDIA_QUICKSTART.md
        rm -f OPTIMIZATION_REPORT.md PIPELINE_COMPARISON.md ETL_COMPLETION_SUMMARY.md
        rm -f RDF_CONVERSION_GUIDE.md RDF_DATABASE_OPTIONS.md

        echo -e "${GREEN}✅ Old files deleted${NC}\n"
    else
        echo -e "${YELLOW}Skipped deletion. Old files kept.${NC}\n"
    fi
}

# Main menu
case "${1:-menu}" in
    backup)
        create_backup
        ;;
    consolidate)
        consolidate_docs
        ;;
    show)
        show_deletable_files
        ;;
    delete)
        delete_old_files
        ;;
    all)
        create_backup
        consolidate_docs
        show_deletable_files
        delete_old_files
        ;;
    *)
        echo "Usage: $0 [backup|consolidate|show|delete|all]"
        echo ""
        echo "Commands:"
        echo "  backup       - Create git backup branch"
        echo "  consolidate  - Merge documentation files into docs/"
        echo "  show         - Show which files can be deleted"
        echo "  delete       - Delete old files (with confirmation)"
        echo "  all          - Run all steps in sequence"
        echo ""
        echo "Example: $0 consolidate"
        ;;
esac

echo -e "${GREEN}Done!${NC}"
