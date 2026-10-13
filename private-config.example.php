<?php

return [
    'captcha_secret' => 'REPLACE_WITH_YANDEX_CAPTCHA_SECRET',
    'captcha_hostnames' => [
        'forum-dance.ru',
        'www.forum-dance.ru',
    ],
    'allowed_origins' => [
        'https://forum-dance.ru',
        'https://www.forum-dance.ru',
    ],
    'admin_password_hash' => 'REPLACE_WITH_PASSWORD_HASH',
    'mail_to' => [
        'forumdance@mail.ru',
        'maksiml.04@mail.ru',
    ],
    'mail_from' => 'noreply@forum-dance.ru',
    'log_file' => __DIR__ . '/submissions.log',
    'rate_limit_dir' => __DIR__ . '/form-rate-limit',
];
