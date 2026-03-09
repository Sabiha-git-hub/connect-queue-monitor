#!/bin/bash

# Create deployment package for Elastic Beanstalk
# Usage: ./scripts/create_deployment_package.sh [package-name]

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get package name from argument or use default
PACKAGE_NAME=${1:-app}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ZIP_NAME="${PACKAGE_NAME}_${TIMESTAMP}.zip"

echo -e "${GREEN}Creating deployment package: ${ZIP_NAME}${NC}"

# Check if we're in the project root
if [ ! -f "run.py" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo -e "${YELLOW}Using temporary directory: ${TEMP_DIR}${NC}"

# Copy application files
echo -e "${YELLOW}Copying application files...${NC}"
cp -r app/ "${TEMP_DIR}/"
cp -r config/ "${TEMP_DIR}/"
cp run.py "${TEMP_DIR}/"
cp requirements.txt "${TEMP_DIR}/"
cp Procfile "${TEMP_DIR}/"

# Copy Elastic Beanstalk configuration
echo -e "${YELLOW}Copying Elastic Beanstalk configuration...${NC}"
cp -r .ebextensions/ "${TEMP_DIR}/"
cp -r .platform/ "${TEMP_DIR}/"

# Create zip file
echo -e "${YELLOW}Creating zip file...${NC}"
cd "${TEMP_DIR}"
zip -r "${ZIP_NAME}" . -x "*.pyc" -x "__pycache__/*" -x ".DS_Store"

# Move zip to project root
mv "${ZIP_NAME}" "${OLDPWD}/"
cd "${OLDPWD}"

# Cleanup
rm -rf "${TEMP_DIR}"

# Show file size
FILE_SIZE=$(du -h "${ZIP_NAME}" | cut -f1)
echo -e "${GREEN}✓ Deployment package created: ${ZIP_NAME} (${FILE_SIZE})${NC}"

# Show deployment instructions
echo ""
echo -e "${GREEN}Deployment Instructions:${NC}"
echo "1. Upload to Elastic Beanstalk:"
echo "   eb deploy"
echo ""
echo "2. Or upload manually:"
echo "   - Go to Elastic Beanstalk console"
echo "   - Select your environment"
echo "   - Click 'Upload and deploy'"
echo "   - Choose ${ZIP_NAME}"
echo ""
echo "3. After deployment, invalidate CloudFront cache (if frontend changed):"
echo "   aws cloudfront create-invalidation --distribution-id E2ZQ9PY5KN8UMB --paths '/*'"
echo ""
echo -e "${YELLOW}Note: CloudFront invalidation only needed for HTML/CSS/JS/image changes${NC}"
