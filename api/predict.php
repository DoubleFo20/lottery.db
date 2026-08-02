<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
set_time_limit(180);

header("Content-Type: application/json; charset=utf-8");
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, OPTIONS");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

$BASE_DIR       = realpath(__DIR__ . '/..');
$CACHE_FILE     = $BASE_DIR . '/database/predictions/pipeline_cache.json';
$CSV_FILE       = $BASE_DIR . '/database/dataset/lottery_history.csv';
$PIPELINE       = $BASE_DIR . '/api/run_pipeline.py';
$RESULT_FETCHER = $BASE_DIR . '/analytics/result_fetcher.py';
$PYTHON         = 'python';

function respond_json($payload, $code = 200) {
    http_response_code($code);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
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
        return [
            'exists' => false,
            'total_draws' => 0,
            'latest' => null,
            'mtime' => null,
        ];
    }

    $fh = fopen($csvFile, 'r');
    $headers = fgetcsv($fh);
    $rows = [];
    while (($row = fgetcsv($fh)) !== false) {
        if (!$headers || count($row) === 0 || trim($row[0] ?? '') === '') {
            continue;
        }
        $rows[] = array_combine($headers, array_pad($row, count($headers), ''));
    }
    fclose($fh);

    usort($rows, fn($a, $b) => strcmp($b['draw_date'] ?? '', $a['draw_date'] ?? ''));
    $latest = $rows[0] ?? null;

    return [
        'exists' => true,
        'total_draws' => count($rows),
        'latest' => $latest,
        'mtime' => date('c', filemtime($csvFile)),
    ];
}

function read_cache($cacheFile) {
    if (!file_exists($cacheFile) || filesize($cacheFile) === 0) {
        return null;
    }
    return json_decode(file_get_contents($cacheFile), true);
}

$action  = strtolower(trim($_GET['action'] ?? 'predict'));
$refresh = intval($_GET['refresh'] ?? 0);
$top     = max(1, min(20, intval($_GET['top'] ?? 5)));
$beam    = max(2, min(6, intval($_GET['beam'] ?? 3)));
$window  = max(10, min(200, intval($_GET['window'] ?? 50)));

if ($action === 'fetch_result') {
    $cmd = "{$PYTHON} " . escapeshellarg($RESULT_FETCHER) . " 2>&1";
    $fetch = run_command($cmd);
    $cacheMtimeBefore = file_exists($CACHE_FILE) ? filemtime($CACHE_FILE) : 0;

    $pipeline = null;
    if (file_exists($CSV_FILE) && (!file_exists($CACHE_FILE) || filemtime($CSV_FILE) > $cacheMtimeBefore)) {
        $pipelineCmd = "{$PYTHON} " . escapeshellarg($PIPELINE)
            . " --top {$top} --beam {$beam} --window {$window} 2>&1";
        $pipeline = run_command($pipelineCmd);
    }

    respond_json([
        'status' => 'ok',
        'action' => 'fetch_result',
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

if ($action === 'run_pipeline') {
    $cmd = "{$PYTHON} " . escapeshellarg($PIPELINE)
        . " --top {$top} --beam {$beam} --window {$window} 2>&1";
    $result = run_command($cmd);

    respond_json([
        'status' => file_exists($CACHE_FILE) ? 'ok' : 'error',
        'action' => 'run_pipeline',
        'message' => file_exists($CACHE_FILE) ? 'Pipeline cache regenerated.' : 'Pipeline failed to generate cache.',
        'result' => $result,
        'dataset' => read_dataset_status($CSV_FILE),
        'cache' => file_exists($CACHE_FILE) ? [
            'cached_at' => date('c', filemtime($CACHE_FILE)),
            'age_seconds' => time() - filemtime($CACHE_FILE),
        ] : null,
    ], file_exists($CACHE_FILE) ? 200 : 500);
}

if ($action === 'status') {
    respond_json([
        'status' => 'ok',
        'endpoint' => 'status',
        'dataset' => read_dataset_status($CSV_FILE),
        'cache' => file_exists($CACHE_FILE) ? [
            'cached_at' => date('c', filemtime($CACHE_FILE)),
            'age_seconds' => time() - filemtime($CACHE_FILE),
        ] : null,
    ]);
}

if ($refresh || !file_exists($CACHE_FILE) || (file_exists($CSV_FILE) && file_exists($CACHE_FILE) && filemtime($CSV_FILE) > filemtime($CACHE_FILE))) {
    $cmd = "{$PYTHON} " . escapeshellarg($PIPELINE)
        . " --top {$top} --beam {$beam} --window {$window} 2>&1";
    $output = shell_exec($cmd);

    if (!file_exists($CACHE_FILE)) {
        respond_json([
            'status' => 'error',
            'message' => 'Pipeline failed to generate cache',
            'cmd' => $cmd,
            'output' => substr($output ?? '', 0, 1200),
        ], 500);
    }
}

$data = read_cache($CACHE_FILE);
if ($data === null) {
    respond_json([
        'status' => 'error',
        'message' => 'Cache file is missing or not valid JSON',
    ], 500);
}

$dataset = read_dataset_status($CSV_FILE);
$data['status'] = $data['status'] ?? 'ok';
$data['dataset'] = $dataset;
$data['cache'] = [
    'cached_at' => date('c', filemtime($CACHE_FILE)),
    'age_seconds' => time() - filemtime($CACHE_FILE),
    'hint' => 'Add ?refresh=1 to regenerate predictions',
];
$data['meta']['dataset'] = [
    'total_draws' => $dataset['total_draws'],
    'latest' => $dataset['latest']['draw_date'] ?? null,
    'latest_number' => $dataset['latest']['first_prize'] ?? null,
];

respond_json($data);
