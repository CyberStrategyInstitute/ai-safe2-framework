
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('data/controls.json', 'utf8'));
const ids = data.map(c => c.id);
const counts = {};
ids.forEach(id => {
  counts[id] = (counts[id] || 0) + 1;
});
Object.keys(counts).forEach(id => {
  if (counts[id] > 1) {
    console.log(`Duplicate ID: ${id} (${counts[id]} times)`);
  }
});
console.log(`Total controls: ${data.length}`);
