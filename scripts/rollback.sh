#!/bin/bash
# Zero Tolerance - Rollback from .bak files
# بازگشت سریع با استفاده از فایل‌های backup

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Options
WHAT_IF=0
VERBOSE=0
PATH_ARG="."

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --what-if)
            WHAT_IF=1
            shift
            ;;
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
        --path)
            PATH_ARG="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}🔄 Zero Tolerance Rollback Tool${NC}"
echo -e "${CYAN}================================${NC}"
echo ""

count=0
errors=0

# Find all .bak files and restore
find "$PATH_ARG" -name "*.bak" -print0 2>/dev/null | while IFS= read -r -d '' bak_file; do
    orig_file="${bak_file%.bak}"
    
    if [ $VERBOSE -eq 1 ]; then
        echo -e "${CYAN}Found: $bak_file${NC}"
    fi
    
    if [ -f "$orig_file" ]; then
        if [ $WHAT_IF -eq 1 ]; then
            echo -e "${YELLOW}[DRY-RUN] Would restore: $orig_file${NC}"
            ((count++))
        else
            if cp "$bak_file" "$orig_file"; then
                echo -e "${GREEN}✅ Restored: $orig_file${NC}"
                ((count++))
            else
                echo -e "${RED}❌ Failed: $orig_file${NC}"
                ((errors++))
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  Original not found: $orig_file${NC}"
    fi
done

echo ""
echo -e "${CYAN}================================${NC}"

if [ $WHAT_IF -eq 1 ]; then
    echo -e "${YELLOW}🔍 Dry-run complete: Would restore $count files${NC}"
else
    echo -e "${GREEN}✅ Rollback complete: $count files restored${NC}"
    if [ $errors -gt 0 ]; then
        echo -e "${RED}⚠️  Errors: $errors files failed${NC}"
    fi
fi

echo ""
