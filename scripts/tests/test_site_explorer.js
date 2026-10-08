#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');
const html = fs.readFileSync(path.join(root, 'site/index.html'), 'utf8');
const scriptStart = html.lastIndexOf('<script>') + '<script>'.length;
const scriptEnd = html.lastIndexOf('</script>');
const fullScript = html.slice(scriptStart, scriptEnd);
new Function(fullScript);

const allRows = JSON.parse(fs.readFileSync(path.join(root, 'site/data/results.json'), 'utf8')).results;
const presetCards = JSON.parse(fs.readFileSync(path.join(root, 'site/data/presets.json'), 'utf8')).presets;
const communityRows = allRows.filter((row) => row.source?.label === 'community-3x5060ti-mvdevnull');

const slice = (start, end) => {
  const from = html.indexOf(start);
  const to = html.indexOf(end, from);
  if (from < 0 || to < 0) throw new Error(`missing explorer code block: ${start}`);
  return html.slice(from, to);
};

const code = [
  slice('    const get =', '    const unique ='),
  slice('    const displayMetric =', '    const resultLabels ='),
  slice('    const normalizeGpuModel =', '    const escapeHtml ='),
  slice('    const effectiveReasoningBudget =', '    const formatThinkingLabel ='),
  slice('    const groupKey =', '    const buildHardwareLane ='),
].join('\n');

const closeEnough = (actual, expected) => Math.abs(actual - expected) < 0.0001;

eval(code + `
  const hardwareLabels = [...new Set(allRows.map(gpuFilterLabel))].sort();
  const expectedHardware = ['1x RTX 5060 Ti', '2x RTX 5060 Ti', '3x RTX 5060 Ti', 'Mixed 5060 Ti + CUDA'];
  if (JSON.stringify(hardwareLabels) !== JSON.stringify(expectedHardware)) {
    throw new Error('hardware filters do not normalize: ' + JSON.stringify(hardwareLabels));
  }

  const collapsed = collapseRepeatedRuns(communityRows);
  if (collapsed.length !== 2) throw new Error('expected 2 community prompt rows, got ' + collapsed.length);
  if (!collapsed.every((row) => row._run_count === 2)) throw new Error('community repeats were not collapsed');

  const short = collapsed.find((row) => row.benchmark.prompt_set === 'short-chat');
  const long = collapsed.find((row) => row.benchmark.prompt_set === 'long-retrieval');
  if (!closeEnough(short._avg_decode_tok_s, 30.4605)) throw new Error('short decode average mismatch');
  if (!closeEnough(long._avg_decode_tok_s, 24.217)) throw new Error('long decode average mismatch');
  if (!closeEnough(long._avg_prompt_tok_s, 479.5625)) throw new Error('long prompt average mismatch');
  if (!closeEnough(decodeTokS(short), 30.465)) throw new Error('selected short decode metric mismatch');
  if (!closeEnough(promptTokS(long), 479.541)) throw new Error('selected long prompt metric mismatch');

  const presetMap = presetEvidenceByEngine(presetCards);
  const ninfer = presetMap.get('NInfer');
  if (!ninfer || ninfer.bestContext !== 262144) throw new Error('NInfer preset evidence missing from engine summary');
  for (const [engine, entry] of presetMap) {
    if (!(entry.bestDecode > 0) || !(entry.bestContext > 0) || !entry.presets.size) throw new Error('bad preset evidence entry for ' + engine);
  }
  if (presetEvidenceByEngine([]).size !== 0) throw new Error('empty preset list should give empty map');
`);

console.log('site explorer contribution presentation test passed');
