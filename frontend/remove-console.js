const fs = require('fs');
const path = require('path');

/**
 * Script to remove console.log statements from production build
 * Usage: node remove-console.js
 */

const distFolder = path.join(__dirname, 'dist', 'advance-company-frontend', 'browser');

function removeConsoleLogs(filePath) {
  try {
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Remove various console statements
    const patterns = [
      /console\.log\([^)]*\);?/g,
      /console\.warn\([^)]*\);?/g,
      /console\.error\([^)]*\);?/g,
      /console\.info\([^)]*\);?/g,
      /console\.debug\([^)]*\);?/g,
      /console\.table\([^)]*\);?/g,
      /console\.group\([^)]*\);?/g,
      /console\.groupEnd\([^)]*\);?/g,
      /console\.trace\([^)]*\);?/g,
      /console\.dir\([^)]*\);?/g,
      /console\.time\([^)]*\);?/g,
      /console\.timeEnd\([^)]*\);?/g,
    ];

    patterns.forEach(pattern => {
      content = content.replace(pattern, '');
    });

    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`✓ Removed console logs from: ${path.basename(filePath)}`);
  } catch (error) {
    console.error(`✗ Error processing ${filePath}:`, error.message);
  }
}

function processDirectory(directory) {
  if (!fs.existsSync(directory)) {
    console.log('Build directory not found. Please run "npm run build:prod" first.');
    return;
  }

  console.log('🧹 Cleaning console logs from production build...\n');

  const files = fs.readdirSync(directory);
  let processedCount = 0;

  files.forEach(file => {
    const filePath = path.join(directory, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      processDirectory(filePath);
    } else if (file.endsWith('.js')) {
      removeConsoleLogs(filePath);
      processedCount++;
    }
  });

  if (processedCount > 0) {
    console.log(`\n Successfully processed ${processedCount} JavaScript files`);
  }
}

// Run the script
processDirectory(distFolder);