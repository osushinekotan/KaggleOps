#!/bin/bash

set -e

echo "🔍 Scraping Kaggle competition data..."

# Check if TAVILY_API_KEY is set
if [ -z "$TAVILY_API_KEY" ]; then
    echo "❌ TAVILY_API_KEY environment variable is not set"
    exit 1
fi

# Check if KAGGLE_COMPETITION_NAME is set
if [ -z "$KAGGLE_COMPETITION_NAME" ]; then
    echo "❌ KAGGLE_COMPETITION_NAME environment variable is not set"
    exit 1
fi

# Convert competition name to lowercase for URL
COMPETITION_NAME_LOWER=$(echo "$KAGGLE_COMPETITION_NAME" | tr '[:upper:]' '[:lower:]')

# Create docs directory
DOCS_DIR="docs/$KAGGLE_COMPETITION_NAME"
mkdir -p "$DOCS_DIR"

echo "📂 Created directory: $DOCS_DIR"
echo "🏆 Competition: $KAGGLE_COMPETITION_NAME"

# Function to scrape and save content
scrape_page() {
    local page_type="$1"
    local url="https://www.kaggle.com/competitions/$COMPETITION_NAME_LOWER/$page_type"
    local output_file="$DOCS_DIR/$page_type.md"
    
    echo "🌐 Scraping $page_type from: $url"
    
    # Make API call to Tavily
    response=$(curl -s -X POST https://api.tavily.com/extract \
        -H 'Content-Type: application/json' \
        -H "Authorization: Bearer $TAVILY_API_KEY" \
        -d "{
            \"urls\": [\"$url\"],
            \"extract_depth\": \"advanced\"
        }")
    
    # Check if curl was successful
    if [ $? -ne 0 ]; then
        echo "❌ Failed to scrape $page_type"
        return 1
    fi
    
    # Extract content from JSON response using jq (if available) or basic parsing
    if command -v jq >/dev/null 2>&1; then
        content=$(echo "$response" | jq -r '.results[0].raw_content // empty')
    else
        # Basic parsing without jq - extract raw_content field
        content=$(echo "$response" | sed -n 's/.*"raw_content":"\([^"]*\)".*/\1/p' | head -1)
    fi
    
    if [ -z "$content" ] || [ "$content" = "null" ]; then
        echo "⚠️  No content found for $page_type"
        echo "Response: $response"
        return 1
    fi
    
    # Create markdown file with header
    page_title=$(echo "$page_type" | sed 's/^./\U&/')
    echo "# $KAGGLE_COMPETITION_NAME - $page_title" > "$output_file"
    echo "" >> "$output_file"
    
    # Unescape JSON content and add to file
    echo "$content" | sed 's/\\n/\n/g' | sed 's/\\t/\t/g' | sed 's/\\"/"/g' >> "$output_file"
    
    echo "✅ Saved: $output_file"
}

# Scrape overview page
scrape_page "overview"

# Scrape data page
scrape_page "data"

echo "🎉 Competition data scraping completed!"
echo "📁 Files saved in: $DOCS_DIR/"