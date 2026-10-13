<?php

$privateConfigPath = dirname(__DIR__, 2) . '/private-config.php';
if (!is_readable($privateConfigPath)) {
    http_response_code(500);
    exit('Server configuration is unavailable');
}

$privateConfig = require $privateConfigPath;
if (!is_array($privateConfig) || empty($privateConfig['admin_password_hash'])) {
    http_response_code(500);
    exit('Server configuration is invalid');
}

define('ADMIN_PASSWORD_HASH', $privateConfig['admin_password_hash']);
define('DATA_FILE', __DIR__ . '/../content.json');
define('BUILD_SCRIPT', __DIR__ . '/../build.py');
define('NEWS_DIR', __DIR__ . '/../userfls/news');
define('SITE_URL', 'https://forum-dance.ru');
