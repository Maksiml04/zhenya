<?php

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

function respond(int $status, array $payload): never
{
    http_response_code($status);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

$configPath = dirname(__DIR__, 3) . '/private-config.php';
if (!is_readable($configPath)) {
    respond(500, ['error' => 'Server configuration is unavailable']);
}

$config = require $configPath;
if (!is_array($config)) {
    respond(500, ['error' => 'Server configuration is invalid']);
}

$allowedOrigins = $config['allowed_origins'] ?? [];
$origin = trim((string) ($_SERVER['HTTP_ORIGIN'] ?? ''));
if ($origin !== '' && !in_array($origin, $allowedOrigins, true)) {
    respond(403, ['error' => 'Origin is not allowed']);
}

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    if ($origin !== '') {
        header('Access-Control-Allow-Origin: ' . $origin);
        header('Vary: Origin');
    }
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond(405, ['error' => 'Method not allowed']);
}

$name = trim((string) ($_POST['name'] ?? ''));
$phone = trim((string) ($_POST['phone'] ?? ''));
$direction = trim((string) ($_POST['direction'] ?? ''));
$token = trim((string) ($_POST['cf-turnstile-response'] ?? ''));

if ($name === '' || strlen($name) > 120) {
    respond(422, ['error' => 'Invalid name']);
}
if ($phone === '' || strlen($phone) > 40 || preg_match('/\D/', $phone) === 1 || strlen(preg_replace('/\D/', '', $phone)) < 10) {
    respond(422, ['error' => 'Invalid phone']);
}
if (strlen($direction) > 120 || preg_match('/[\r\n]/', $name . $phone . $direction)) {
    respond(422, ['error' => 'Invalid form data']);
}
if ($token === '' || strlen($token) > 2048) {
    respond(400, ['error' => 'Missing captcha']);
}

$rateLimitDir = $config['rate_limit_dir'] ?? dirname(__DIR__, 3) . '/form-rate-limit';
if (!is_dir($rateLimitDir)) {
    @mkdir($rateLimitDir, 0700, true);
}
$clientIp = (string) ($_SERVER['REMOTE_ADDR'] ?? 'unknown');
$rateFile = rtrim($rateLimitDir, '/') . '/' . hash('sha256', $clientIp);
if (is_file($rateFile) && time() - (int) @file_get_contents($rateFile) < 60) {
    respond(429, ['error' => 'Too many requests']);
}
@file_put_contents($rateFile, (string) time(), LOCK_EX);

$ch = curl_init('https://challenges.cloudflare.com/turnstile/v0/siteverify');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => http_build_query([
        'secret' => (string) ($config['turnstile_secret'] ?? ''),
        'response' => $token,
    ]),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 10,
    CURLOPT_SSL_VERIFYPEER => true,
]);
$response = curl_exec($ch);
$httpCode = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode !== 200 || !is_string($response) || $response === '') {
    respond(502, ['error' => 'Captcha verification failed']);
}

$verification = json_decode($response, true);
$expectedAction = (string) ($config['turnstile_action'] ?? 'submit');
$expectedHosts = $config['turnstile_hostnames'] ?? [];
if (
    !is_array($verification)
    || ($verification['success'] ?? false) !== true
    || ($verification['action'] ?? '') !== $expectedAction
    || !in_array(($verification['hostname'] ?? ''), $expectedHosts, true)
) {
    respond(403, ['error' => 'Captcha verification rejected']);
}

$nameHtml = htmlspecialchars($name, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
$phoneHtml = htmlspecialchars($phone, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
$directionHtml = htmlspecialchars($direction !== '' ? $direction : 'Не указано', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
$submittedAt = date('Y-m-d H:i:s');
$subject = 'Новая заявка с сайта Форум';
$message = <<<HTML
<h2>Новая заявка</h2>
<table style="border-collapse:collapse;width:100%;max-width:500px">
<tr style="background:#f5f5f5"><td style="padding:10px;font-weight:600">Имя</td><td style="padding:10px">{$nameHtml}</td></tr>
<tr><td style="padding:10px;font-weight:600">Телефон</td><td style="padding:10px">{$phoneHtml}</td></tr>
<tr style="background:#f5f5f5"><td style="padding:10px;font-weight:600">Направление</td><td style="padding:10px">{$directionHtml}</td></tr>
<tr><td style="padding:10px;font-weight:600">Время</td><td style="padding:10px">{$submittedAt}</td></tr>
</table>
HTML;

$headers = "MIME-Version: 1.0\r\n";
$headers .= "Content-Type: text/html; charset=utf-8\r\n";
$headers .= 'From: Форум <' . ($config['mail_from'] ?? 'noreply@forum-dance.ru') . ">\r\n";
$recipients = array_values(array_filter($config['mail_to'] ?? [], 'is_string'));
$mailOk = $recipients !== [] && @mail(implode(',', $recipients), $subject, $message, $headers);

$logFile = (string) ($config['log_file'] ?? dirname(__DIR__, 3) . '/submissions.log');
$safeIpHash = substr(hash('sha256', $clientIp), 0, 16);
$logLine = sprintf(
    "[%s] status=%s direction=%s ip_hash=%s\n",
    $submittedAt,
    $mailOk ? 'accepted' : 'mail_failed',
    str_replace(["\r", "\n"], ' ', $direction !== '' ? $direction : 'none'),
    $safeIpHash
);
@file_put_contents($logFile, $logLine, FILE_APPEND | LOCK_EX);

if (!$mailOk) {
    respond(502, ['error' => 'Mail delivery failed']);
}

respond(200, ['success' => true, 'message' => 'Заявка принята']);
