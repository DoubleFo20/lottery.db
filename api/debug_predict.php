<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
header("Content-Type: text/plain; charset=utf-8");

echo "=== DEBUG PREDICT ===\n\n";

// 1. Check PHP version
echo "PHP version: " . phpversion() . "\n";

// 2. Check if shell_exec is available
$disabled = ini_get('disable_functions');
echo "Disabled functions: " . ($disabled ?: 'none') . "\n\n";

$shell_ok = !in_array('shell_exec', array_map('trim', explode(',', $disabled)));
echo "shell_exec available: " . ($shell_ok ? 'YES' : 'NO') . "\n";

// 3. Check Python
if ($shell_ok) {
    $py_version = shell_exec('python --version 2>&1');
    echo "Python: " . trim($py_version) . "\n";
} else {
    echo "Python: CANNOT CHECK (shell_exec disabled)\n";
}

// 4. Check CSV
$csv = realpath(__DIR__ . '/../database/dataset/lottery_history.csv');
echo "CSV exists: " . (file_exists($csv) ? "YES ({$csv})" : "NO") . "\n";

// 5. Check predictor script
$predictor = realpath(__DIR__ . '/../ensemble_model/predictor.py');
echo "Predictor exists: " . (file_exists($predictor) ? "YES" : "NO") . "\n";

// 6. Try a simple Python command
if ($shell_ok) {
    echo "\n--- Running: python -c \"print('hello')\" ---\n";
    $test = shell_exec('python -c "print(\'hello\')" 2>&1');
    echo "Result: " . ($test ?: 'NULL/empty') . "\n";

    echo "\n--- Running predictor (--json --top 1 --beam 2) ---\n";
    $cmd = 'python ' . escapeshellarg($predictor) . ' --json --top 1 --beam 2 2>&1';
    echo "CMD: {$cmd}\n";
    $result = shell_exec($cmd);
    echo "Output length: " . strlen($result) . "\n";
    echo "First 500 chars:\n" . substr($result, 0, 500) . "\n";
}

echo "\n=== DONE ===\n";
