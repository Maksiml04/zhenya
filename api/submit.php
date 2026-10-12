<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$secret = '0x4AAAAAAFUJ0hxWgUymAS_UdwZxgdEypKs';

$name = trim($_POST['name'] ?? '');
$phone = trim($_POST['phone'] ?? '');
$direction = trim($_POST['direction'] ?? '');
$token = trim($_POST['cf-turnstile-response'] ?? '');

if (!$token) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing captcha']);
    exit;
}

$ip = $_SERVER['REMOTE_ADDR'] ?? '';

$ch = curl_init('https://challenges.cloudflare.com/turnstile/v0/siteverify');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => http_build_query([
        'secret' => $secret,
        'response' => $token,
        'remoteip' => $ip,
    ]),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 10,
    CURLOPT_SSL_VERIFYPEER => true,
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode !== 200 || !$response) {
    http_response_code(502);
    echo json_encode(['error' => 'Captcha verification failed']);
    exit;
}

$result = json_decode($response, true);

if (!$result || !($result['success'] ?? false)) {
    http_response_code(403);
    echo json_encode(['error' => 'Captcha verification rejected']);
    exit;
}

$log = sprintf(
    "[%s] Имя: %s | Телефон: %s | Направление: %s | IP: %s\n",
    date('Y-m-d H:i:s'),
    $name,
    $phone,
    $direction,
    $ip
);

$logFile = __DIR__ . '/../submissions.log';
@file_put_contents($logFile, $log, FILE_APPEND | LOCK_EX);

echo json_encode(['success' => true, 'message' => 'Заявка принята']);
