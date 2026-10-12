<?php
require_once __DIR__ . '/config.php';

session_start();

if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: ?');
    exit;
}

$authed = ($_SESSION['admin'] ?? false);

if ($_SERVER['REQUEST_METHOD'] === 'POST' && !$authed) {
    if (($_POST['password'] ?? '') === ADMIN_PASSWORD) {
        $_SESSION['admin'] = true;
        $authed = true;
    } else {
        $error = 'Неверный пароль';
    }
}

if (!$authed) {
    ?>
    <!DOCTYPE html>
    <html lang="ru">
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Вход — Админ-панель</title>
    <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f0f0;display:flex;align-items:center;justify-content:center;min-height:100vh}
    .login{background:#fff;padding:32px;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.08);width:340px}
    h1{font-size:1.2rem;margin-bottom:20px}
    input{width:100%;padding:10px 12px;border:1.5px solid #ddd;border-radius:8px;font-size:1rem;margin-bottom:12px}
    button{width:100%;padding:10px;background:#111;color:#fff;border:none;border-radius:8px;font-size:1rem;cursor:pointer}
    .err{color:#dc2626;font-size:.9rem;margin-bottom:12px}
    </style>
    </head>
    <body>
    <form class="login" method="post">
    <h1>Админ-панель</h1>
    <?php if (isset($error)) echo "<div class=\"err\">$error</div>" ?>
    <input type="password" name="password" placeholder="Пароль" required autofocus>
    <button type="submit">Войти</button>
    </form>
    </body>
    </html>
    <?php
    exit;
}

$data = json_decode(file_get_contents(DATA_FILE), true);
$newsItems = &$data['news']['items'];
$newsDetails = &$data['news']['details'];
$action = $_GET['action'] ?? 'list';
$slug = $_GET['slug'] ?? '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $authed) {
    $title = trim($_POST['title'] ?? '');
    $date = trim($_POST['date'] ?? '');
    $body = trim($_POST['body'] ?? '');
    $editSlug = $_POST['edit_slug'] ?? '';

    if ($title) {
        $newSlug = $editSlug ?: 'news-' . time();
        $newsItem = [
            'slug' => $newSlug,
            'route' => "news/$newSlug",
            'title' => $title,
            'date' => $date ?: date('d.m.Y'),
            'thumb' => '',
        ];

        $newsDetail = [
            'title' => $title,
            'body_html' => $body,
            'gallery' => [],
        ];

        if (!empty($_FILES['image']['name'])) {
            $ext = strtolower(pathinfo($_FILES['image']['name'], PATHINFO_EXTENSION));
            if (in_array($ext, ['jpg', 'jpeg', 'png', 'webp'])) {
                $imgName = time() . '_' . md5($_FILES['image']['name']) . ".$ext";
                $smallDir = NEWS_DIR . '/small';
                $mediumDir = NEWS_DIR . '/medium';
                @mkdir($smallDir, 0755, true);
                @mkdir($mediumDir, 0755, true);

                $origPath = $_FILES['image']['tmp_name'];
                $smallPath = "$smallDir/$imgName";
                $mediumPath = "$mediumDir/$imgName";

                copy($origPath, $mediumPath);

                $size = getimagesize($origPath);
                $srcW = $size[0];
                $srcH = $size[1];
                $thumbW = 180;
                $thumbH = round($srcH * ($thumbW / $srcW));

                $srcImg = imagecreatefromstring(file_get_contents($origPath));
                $thumbImg = imagecreatetruecolor($thumbW, $thumbH);
                imagecopyresampled($thumbImg, $srcImg, 0, 0, 0, 0, $thumbW, $thumbH, $srcW, $srcH);

                imagejpeg($thumbImg, $smallPath, 80);
                imagedestroy($srcImg);
                imagedestroy($thumbImg);

                $newsItem['thumb'] = "userfls/news/small/$imgName";

                $newsDetail['gallery'][] = [
                    'full' => "userfls/news/medium/$imgName",
                    'thumb' => "userfls/news/small/$imgName",
                ];
            }
        }

        if ($editSlug && isset($newsDetails[$editSlug])) {
            $old = $newsDetails[$editSlug];
            $newsDetail['gallery'] = $old['gallery'] ?? [];
            if (!empty($_FILES['image']['name']) && !empty($newsDetail['gallery'])) {
                $newsDetail['gallery'][0] = [
                    'full' => "userfls/news/medium/$imgName",
                    'thumb' => "userfls/news/small/$imgName",
                ];
            }

            foreach ($newsItems as &$item) {
                if ($item['slug'] === $editSlug) {
                    $item['title'] = $title;
                    $item['date'] = $newsItem['date'];
                    if ($newsItem['thumb']) $item['thumb'] = $newsItem['thumb'];
                    break;
                }
            }
            unset($item);
            $newsDetails[$editSlug] = $newsDetail;
        } else {
            array_unshift($newsItems, $newsItem);
            $newsDetails[$newSlug] = $newsDetail;
        }

        file_put_contents(DATA_FILE, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));

        $output = '';
        $exitCode = 0;
        $cmd = 'cd ' . escapeshellarg(dirname(DATA_FILE)) . ' && python3 ' . escapeshellarg(BUILD_SCRIPT) . ' 2>&1';
        exec($cmd, $output, $exitCode);

        $buildMsg = $exitCode === 0 ? 'Сайт пересобран' : 'Ошибка сборки';
        $buildOutput = implode("\n", $output);
    }

    header('Location: ?slug=' . urlencode($newSlug ?? '') . '&saved=1');
    exit;
}

if (isset($_GET['delete']) && $authed) {
    $delSlug = $_GET['delete'];
    $newsItems = array_values(array_filter($newsItems, fn($i) => $i['slug'] !== $delSlug));
    unset($newsDetails[$delSlug]);
    file_put_contents(DATA_FILE, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    $cmd = 'cd ' . escapeshellarg(dirname(DATA_FILE)) . ' && python3 ' . escapeshellarg(BUILD_SCRIPT) . ' 2>&1';
    exec($cmd);
    header('Location: ?deleted=1');
    exit;
}

$editItem = null;
$bodyValue = '';
if ($slug && isset($newsDetails[$slug])) {
    foreach ($newsItems as $item) {
        if ($item['slug'] === $slug) {
            $editItem = $item;
            break;
        }
    }
    $bodyValue = $newsDetails[$slug]['body_html'] ?? '';
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Админ-панель — Новости</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;color:#111;font-size:15px;line-height:1.5}
.header{background:#111;color:#fff;padding:14px 24px;display:flex;justify-content:space-between;align-items:center}
.header a{color:#aaa;text-decoration:none;font-size:.9rem}
.header a:hover{color:#fff}
.wrap{max-width:960px;margin:0 auto;padding:24px}
.card{background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.04)}
.card h2{font-size:1.1rem;margin-bottom:12px}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:8px 6px;border-bottom:1px solid #eee;vertical-align:middle}
th{font-size:.8rem;text-transform:uppercase;color:#888;font-weight:600}
td{font-size:.92rem}
.actions{display:flex;gap:6px}
.btn{display:inline-block;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:.85rem;border:none;cursor:pointer;transition:background .15s}
.btn-primary{background:#111;color:#fff}
.btn-primary:hover{background:#333}
.btn-outline{background:transparent;color:#111;border:1px solid #ddd}
.btn-outline:hover{border-color:#111}
.btn-danger{background:#dc2626;color:#fff}
.btn-danger:hover{background:#b91c1c}
label{display:block;font-weight:600;font-size:.85rem;margin-bottom:4px;margin-top:12px}
input,textarea,select{width:100%;padding:8px 10px;border:1.5px solid #ddd;border-radius:6px;font-size:.92rem;font-family:inherit}
textarea{min-height:200px;resize:vertical}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.msg{padding:10px 14px;border-radius:8px;margin-bottom:16px;font-size:.9rem}
.msg-ok{background:#d1fae5;color:#065f46}
.msg-del{background:#fee2e2;color:#991b1b}
small{color:#888}
img.preview{max-width:100px;border-radius:4px;margin-top:4px}
</style>
</head>
<body>
<div class="header">
<div><strong>Админ-панель</strong></div>
<div><a href="?logout=1">Выйти</a></div>
</div>
<div class="wrap">

<?php if (isset($_GET['saved'])): ?>
<div class="msg msg-ok">✓ Новость сохранена, сайт пересобран</div>
<?php endif; ?>
<?php if (isset($_GET['deleted'])): ?>
<div class="msg msg-del">✕ Новость удалена</div>
<?php endif; ?>

<div class="card">
<h2>Новости</h2>
<p style="margin-bottom:12px;color:#888;font-size:.9rem">Нажмите «Добавить» или кликните на заголовок новости для редактирования.</p>
<table>
<thead><tr><th>Дата</th><th>Заголовок</th><th></th></tr></thead>
<tbody>
<?php foreach ($newsItems as $item): ?>
<tr>
<td><small><?= htmlspecialchars($item['date']) ?></small></td>
<td><a href="?slug=<?= urlencode($item['slug']) ?>" style="color:inherit;text-decoration:none"><?= htmlspecialchars($item['title']) ?></a></td>
<td class="actions">
<a class="btn btn-outline" href="?slug=<?= urlencode($item['slug']) ?>" style="padding:4px 10px;font-size:.8rem">✎</a>
<a class="btn btn-danger" href="?delete=<?= urlencode($item['slug']) ?>" style="padding:4px 10px;font-size:.8rem" onclick="return confirm('Удалить новость?')">✕</a>
</td>
</tr>
<?php endforeach; ?>
</tbody>
</table>
<p style="margin-top:12px"><a class="btn btn-primary" href="?action=add">+ Добавить новость</a></p>
</div>

<?php if ($action === 'add' || $editItem): ?>
<div class="card">
<h2><?= $editItem ? 'Редактировать' : 'Добавить новость' ?></h2>
<form method="post" enctype="multipart/form-data">
<?php if ($editItem): ?>
<input type="hidden" name="edit_slug" value="<?= htmlspecialchars($editItem['slug']) ?>">
<?php endif; ?>

<div class="form-row">
<div>
<label>Заголовок</label>
<input type="text" name="title" value="<?= htmlspecialchars($editItem['title'] ?? '') ?>" required>
</div>
<div>
<label>Дата</label>
<input type="text" name="date" value="<?= htmlspecialchars($editItem['date'] ?? date('d.m.Y')) ?>" placeholder="дд.мм.ГГГГ">
</div>
</div>

<label>Текст новости (HTML)</label>
<textarea name="body"><?= htmlspecialchars($bodyValue) ?></textarea>

<label>Изображение</label>
<input type="file" name="image" accept="image/jpeg,image/png,image/webp">
<?php if ($editItem && !empty($newsDetails[$editItem['slug']]['gallery'])): ?>
<br>
<img class="preview" src="../<?= htmlspecialchars($newsDetails[$editItem['slug']]['gallery'][0]['thumb']) ?>" alt="">
<small>текущее изображение</small>
<?php endif; ?>

<div style="margin-top:16px;display:flex;gap:8px">
<button class="btn btn-primary" type="submit"><?= $editItem ? 'Сохранить' : 'Создать' ?></button>
<a class="btn btn-outline" href="?">Отмена</a>
</div>
</form>
</div>
<?php endif; ?>

</div>
</body>
</html>
