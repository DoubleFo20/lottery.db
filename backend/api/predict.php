<?php
/**
 * Prediction REST API
 * ====================
 * Unified backend API for the Lottery AI system.
 *
 * Endpoints (via ?action=):
 *   /predict    GET  Return top candidates from pipeline cache
 *   /history    GET  Return prediction history log
 *   /analytics  GET  Return performance metrics + trend data
 *
 * Usage:
 *   GET backend/api/predict.php?action=predict
 *   GET backend/api/predict.php?action=history
 *   GET backend/api/predict.php?action=analytics
 *   GET backend/api/predict.php?action=predict&refresh=1
 *
 * Optional params:
 *   top=5, beam=3, window=50  (predict only)
 */

error_reporting(E_ALL);
ini_set('display_errors', '0');
set_time_limit(120);

header("Content-Type: application/json; charset=utf-8");
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, OPTIONS");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// ─── Paths ────────────────────────────────────────────────
$BASE_DIR      = realpath(__DIR__ . '/../..');
$PYTHON        = 'python';
$PIPELINE_PY   = $BASE_DIR . '/api/run_pipeline.py';
$RESULT_FETCHER = $BASE_DIR . '/analytics/result_fetcher.py';
$CACHE_FILE    = $BASE_DIR . '/database/predictions/pipeline_cache.json';
$CSV_FILE      = $BASE_DIR . '/database/dataset/lottery_history.csv';
$HISTORY_JSON  = $BASE_DIR . '/database/predictions/prediction_history.json';
$PERF_JSON     = $BASE_DIR . '/performance.json';
$PERF_PY       = $BASE_DIR . '/analytics/performance_analyzer.py';

// ─── Helpers ───────────────────────────────────────────────

function json_ok($data) {
    echo json_encode(array_merge(['status' => 'ok'], $data),
        JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

function json_err($msg, $code = 400) {
    http_response_code($code);
    echo json_encode(['status' => 'error', 'message' => $msg],
        JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

function read_json_file($path) {
    if (!file_exists($path) || filesize($path) === 0) return null;
    return json_decode(file_get_contents($path), true);
}

function run_command($cmd) {
    $started = microtime(true);
    $output = shell_exec($cmd);
    return [
        'cmd' => $cmd,
        'output' => trim($output ?? ''),
        'elapsed_seconds' => round(microtime(true) - $started, 3),
    ];
}

function read_dataset_status($csvFile) {
    if (!file_exists($csvFile) || filesize($csvFile) === 0) {
        return ['exists' => false, 'total_draws' => 0, 'latest' => null, 'mtime' => null];
    }

    $fh = fopen($csvFile, 'r');
    $headers = fgetcsv($fh);
    $rows = [];
    while (($row = fgetcsv($fh)) !== false) {
        if (!$headers || count($row) === 0 || trim($row[0] ?? '') === '') continue;
        $rows[] = array_combine($headers, array_pad($row, count($headers), ''));
    }
    fclose($fh);

    usort($rows, fn($a, $b) => strcmp($b['draw_date'] ?? '', $a['draw_date'] ?? ''));
    return [
        'exists' => true,
        'total_draws' => count($rows),
        'latest' => $rows[0] ?? null,
        'mtime' => date('c', filemtime($csvFile)),
    ];
}

function run_py_json($python, $script, $args = '') {
    $cmd = "{$python} " . escapeshellarg($script) . " --json {$args} 2>NUL";
    $raw = shell_exec($cmd);
    if (!$raw) return null;
    for ($i = 0; $i < strlen($raw); $i++) {
        if ($raw[$i] === '{' || $raw[$i] === '[') {
            return json_decode(substr($raw, $i), true);
        }
    }
    return null;
}

// ─── Router ───────────────────────────────────────────────
$action = strtolower(trim($_GET['action'] ?? 'predict'));


// ══════════════════════════════════════════════════════════
//  ACTION: predict
// ══════════════════════════════════════════════════════════
if ($action === 'predict') {
    $refresh = intval($_GET['refresh'] ?? 0);
    $top     = max(1, min(20, intval($_GET['top']    ?? 5)));
    $beam    = max(2, min(6,  intval($_GET['beam']   ?? 3)));
    $window  = max(10, min(200, intval($_GET['window'] ?? 50)));

    if ($refresh || !file_exists($CACHE_FILE) || (file_exists($CSV_FILE) && file_exists($CACHE_FILE) && filemtime($CSV_FILE) > filemtime($CACHE_FILE))) {
        $cmd = "{$PYTHON} " . escapeshellarg($PIPELINE_PY)
             . " --top {$top} --beam {$beam} --window {$window} 2>&1";
        shell_exec($cmd);
    }

    $cache = read_json_file($CACHE_FILE);
    if (!$cache) {
        json_err('No cache. Run: python api/run_pipeline.py', 503);
    }

    $dataset = read_dataset_status($CSV_FILE);
    json_ok([
        'endpoint'         => 'predict',
        'candidates'       => $cache['candidates']        ?? [],
        'position_scores'  => $cache['position_scores']   ?? [],
        'last_draw'        => $cache['last_draw']         ?? [],
        'ensemble_weights' => $cache['ensemble_weights']  ?? [],
        'explanation'      => $cache['explanation']       ?? null,
        'dataset'          => $dataset,
        'cache' => [
            'cached_at'   => date('c', filemtime($CACHE_FILE)),
            'age_seconds' => time() - filemtime($CACHE_FILE),
            'hint'        => 'Add ?refresh=1 to regenerate',
        ],
        'meta' => array_merge($cache['meta'] ?? [], [
            'dataset' => [
                'total_draws' => $dataset['total_draws'],
                'latest' => $dataset['latest']['draw_date'] ?? null,
                'latest_number' => $dataset['latest']['first_prize'] ?? null,
            ],
        ]),
    ]);
}

elseif ($action === 'run_pipeline') {
    $top     = max(1, min(20, intval($_GET['top']    ?? 5)));
    $beam    = max(2, min(6,  intval($_GET['beam']   ?? 3)));
    $window  = max(10, min(200, intval($_GET['window'] ?? 50)));
    $cmd = "{$PYTHON} " . escapeshellarg($PIPELINE_PY)
         . " --top {$top} --beam {$beam} --window {$window} 2>&1";
    $result = run_command($cmd);

    if (!file_exists($CACHE_FILE)) {
        json_err('Pipeline failed to generate cache', 500);
    }

    json_ok([
        'endpoint' => 'run_pipeline',
        'message' => 'Pipeline cache regenerated.',
        'result' => $result,
        'dataset' => read_dataset_status($CSV_FILE),
        'cache' => [
            'cached_at' => date('c', filemtime($CACHE_FILE)),
            'age_seconds' => time() - filemtime($CACHE_FILE),
        ],
    ]);
}

elseif ($action === 'fetch_result') {
    $before = file_exists($CSV_FILE) ? filemtime($CSV_FILE) : 0;
    $cmd = "{$PYTHON} " . escapeshellarg($RESULT_FETCHER) . " 2>&1";
    $fetch = run_command($cmd);

    $pipeline = null;
    if (file_exists($CSV_FILE) && filemtime($CSV_FILE) > $before) {
        $pipelineCmd = "{$PYTHON} " . escapeshellarg($PIPELINE_PY) . " 2>&1";
        $pipeline = run_command($pipelineCmd);
    }

    json_ok([
        'endpoint' => 'fetch_result',
        'message' => 'Fetch completed. Check output for source/validation details.',
        'fetch' => $fetch,
        'pipeline' => $pipeline,
        'dataset' => read_dataset_status($CSV_FILE),
        'cache' => file_exists($CACHE_FILE) ? [
            'cached_at' => date('c', filemtime($CACHE_FILE)),
            'age_seconds' => time() - filemtime($CACHE_FILE),
        ] : null,
    ]);
}


// ══════════════════════════════════════════════════════════
//  ACTION: history
// ══════════════════════════════════════════════════════════
elseif ($action === 'history') {
    $limit  = max(1, min(100, intval($_GET['limit']  ?? 20)));
    $offset = max(0, intval($_GET['offset'] ?? 0));

    $history = read_json_file($HISTORY_JSON);
    if ($history === null) {
        json_ok(['endpoint' => 'history', 'entries' => [], 'total' => 0,
                 'message'  => 'No history. Run: python analytics/prediction_history.py --log']);
    }

    $total  = count($history);
    $sliced = array_slice(array_reverse($history), $offset, $limit);

    $entries = array_map(function($e) {
        $acc  = $e['accuracy'] ?? null;
        $best = $acc['best']   ?? [];
        return [
            'logged_at'       => $e['logged_at']      ?? '?',
            'target_date'     => $e['target_date']    ?? '?',
            'draw_date_used'  => $e['draw_date_used'] ?? '?',
            'candidates'      => array_map(fn($c) => [
                'number'     => $c['number'],
                'confidence' => $c['confidence'],
            ], $e['candidates'] ?? []),
            'actual_result'   => $e['actual_result']              ?? null,
            'evaluated'       => $acc !== null,
            'exact_match'     => $acc['any_exact_match']          ?? null,
            'best_pos_hits'   => $best['positional_hits']         ?? null,
            'best_digit_hits' => $best['digit_hits']              ?? null,
            'best_candidate'  => $best['candidate']               ?? null,
        ];
    }, $sliced);

    // Summary
    $evaluated = array_filter($history, fn($e) => isset($e['accuracy']));
    $total_pos = 0; $total_dig = 0; $exact_cnt = 0;
    foreach ($evaluated as $e) {
        $b = $e['accuracy']['best'] ?? [];
        $total_pos += $b['positional_hits'] ?? 0;
        $total_dig += $b['digit_hits']      ?? 0;
        if ($e['accuracy']['any_exact_match'] ?? false) $exact_cnt++;
    }
    $ne = count($evaluated);

    json_ok([
        'endpoint' => 'history',
        'total'    => $total,
        'offset'   => $offset,
        'limit'    => $limit,
        'summary'  => [
            'total_logged'        => $total,
            'total_evaluated'     => $ne,
            'exact_matches'       => $exact_cnt,
            'avg_positional_hits' => $ne ? round($total_pos / $ne, 2) : 0,
            'avg_digit_hits'      => $ne ? round($total_dig / $ne, 2) : 0,
        ],
        'entries' => $entries,
    ]);
}


// ══════════════════════════════════════════════════════════
//  ACTION: analytics
// ══════════════════════════════════════════════════════════
elseif ($action === 'analytics') {
    $out = ['endpoint' => 'analytics'];

    // Performance: try saved file first, else run live
    $perf = read_json_file($PERF_JSON) ?? run_py_json($PYTHON, $PERF_PY);
    if ($perf) {
        $out['performance'] = [
            'model_score'    => $perf['model_score']    ?? [],
            'hit_rate'       => $perf['hit_rate']       ?? [],
            'digit_accuracy' => $perf['digit_accuracy'] ?? [],
        ];
    }

    // Trends from prediction cache
    $cache = read_json_file($CACHE_FILE);
    if ($cache) {
        $out['trends']    = $cache['analytics'] ?? [];
        $out['last_draw'] = $cache['last_draw'] ?? [];
        $out['meta']      = $cache['meta']      ?? [];
    }

    $out['generated_at'] = date('c');
    json_ok($out);
}


// ══════════════════════════════════════════════════════════
//  Unknown action → list endpoints
// ══════════════════════════════════════════════════════════
else {
    json_ok([
        'message'   => 'Lottery Prediction API',
        'endpoints' => [
            'predict'   => '?action=predict  [top, beam, window, refresh]',
            'history'   => '?action=history  [limit, offset]',
            'analytics' => '?action=analytics',
        ],
    ]);
}
