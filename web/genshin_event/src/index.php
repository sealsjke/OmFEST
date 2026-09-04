<?php
session_start();

$message = "";
$message_type = "";

if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST["code"])) {
    $code = $_POST["code"];

    if (md5($code) == "0e974114726967211511915142978119") {
        $message = "Билет подтверждён! Флаг: OmFEST{php_3xpl017_1n_2026}";
        $message_type = "success";
    } else {
        $message = "Этот талон недействителен. Попробуйте другой код.";
        $message_type = "error";
    }
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Genshin Impact — Лунная встреча</title>
    <link rel="stylesheet" href="/static/styles/styles.css">
</head>
<body>
    <div class="stars"></div>

    <header class="hero">
        <nav class="nav container">
            <div class="brand">
                <img src="/static/images/paimon.svg" alt="Paimon" class="brand-icon">
                <span>TEYVAT EVENTS</span>
            </div>
            <div class="nav-links">
                <a href="#event">Событие</a>
                <a href="#program">Программа</a>
                <a href="#tickets">Талоны</a>
            </div>
        </nav>

        <div class="hero-content container">
            <div class="eyebrow">НОВОЕ СОБЫТИЕ • МОСКВА • 19:00</div>
            <h1>Лунная<br><span>встреча</span></h1>
            <p class="hero-text">
                Паймон снова что-то задумала. Пора собрать путешественников,
                обменяться историями и встретить новую луну вместе.
            </p>
            <a class="hero-button" href="#tickets">Получить талон</a>
        </div>

        <div class="hero-orb orb-one"></div>
        <div class="hero-orb orb-two"></div>
        <div class="moon"></div>
    </header>

    <main>
        <section id="event" class="section container">
            <div class="section-heading">
                <span>01</span>
                <h2>Что нас ждёт</h2>
            </div>

            <div class="event-grid">
                <article class="glass-card large-card">
                    <div class="card-icon">✦</div>
                    <h3>Вечер путешественников</h3>
                    <p>
                        Небольшая сходка для тех, кто исследует Тейват, спорит
                        о лучших отрядах и всё ещё ищет идеальный артефакт.
                    </p>
                    <div class="meta">19 СЕНТЯБРЯ · 19:00</div>
                </article>

                <article class="glass-card">
                    <div class="card-icon">◈</div>
                    <h3>Турнир</h3>
                    <p>Мини-испытания, викторины и награды для самых внимательных.</p>
                </article>

                <article class="glass-card">
                    <div class="card-icon">☾</div>
                    <h3>Лунная сцена</h3>
                    <p>Музыка, фотографии и свободное общение до позднего вечера.</p>
                </article>
            </div>
        </section>

        <section id="program" class="program-section">
            <div class="container">
                <div class="section-heading">
                    <span>02</span>
                    <h2>Программа</h2>
                </div>

                <div class="timeline">
                    <div class="timeline-item">
                        <time>19:00</time>
                        <div><strong>Открытие ворот</strong><p>Регистрация путешественников и приветствие.</p></div>
                    </div>
                    <div class="timeline-item">
                        <time>19:30</time>
                        <div><strong>Викторина Тейвата</strong><p>Кто действительно знает Ли Юэ и Мондштадт?</p></div>
                    </div>
                    <div class="timeline-item">
                        <time>20:30</time>
                        <div><strong>Турнир</strong><p>Командные испытания и призы.</p></div>
                    </div>
                    <div class="timeline-item">
                        <time>22:00</time>
                        <div><strong>Лунный финал</strong><p>Общее фото и свободная программа.</p></div>
                    </div>
                </div>
            </div>
        </section>

        <section id="tickets" class="tickets-section container">
            <div class="ticket-copy">
                <div class="section-heading">
                    <span>03</span>
                    <h2>Талон путешественника</h2>
                </div>
                <p>
                    У вас есть специальный код? Введите его ниже, чтобы проверить
                    талон на посещение события.
                </p>
                <div class="ticket-note">
                    <span>i</span>
                    <div>
                        <strong>Внимание</strong>
                        <p>Один код — один вход. Паймон очень внимательно проверяет талоны.</p>
                    </div>
                </div>
            </div>

            <div class="ticket">
                <div class="ticket-top">
                    <div>
                        <small>TEYVAT EVENTS</small>
                        <h3>MOONLIGHT<br>MEETUP</h3>
                    </div>
                    <img src="/static/images/paimon.svg" alt="" class="ticket-icon">
                </div>

                <div class="ticket-divider"></div>

                <form method="POST" action="#tickets">
                    <label for="code">Код талона</label>
                    <input
                        id="code"
                        name="code"
                        type="text"
                        autocomplete="off"
                        placeholder="Введите код..."
                        required
                    >
                    <button type="submit">Проверить талон <span>→</span></button>
                </form>

                <?php if ($message !== ""): ?>
                    <div class="result <?= htmlspecialchars($message_type, ENT_QUOTES, "UTF-8") ?>">
                        <?= htmlspecialchars($message, ENT_QUOTES, "UTF-8") ?>
                    </div>
                <?php endif; ?>

                <div class="ticket-footer">
                    <span>19.09.2026</span>
                    <span>МОСКВА</span>
                    <span>19:00</span>
                </div>
            </div>
        </section>
    </main>

    <footer>
        <div class="container">
            <span>TEYVAT EVENTS</span>
            <span>Путешествие только начинается.</span>
        </div>
    </footer>
</body>
</html>
