# -*- coding: utf-8 -*-
import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from config.settings import (
    NVIDIA_API_KEY, NVIDIA_API_URL, NVIDIA_MODEL,
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    REDDIT_USERNAME, REDDIT_PASSWORD, SUBREDDIT_1, SUBREDDIT_2,
    POSTS_PER_DAY, MIN_HOURS_BETWEEN_POSTS, DB_PATH, WORD_FILES_DIR,
    DAILY_POST_LIMIT, TARGET_SUBREDDIT
)
from core.word_parser import WordParser
from core.csv_parser import CSVParser
from core.content_analyzer import ContentAnalyzer
from core.ai_generator import AIGenerator
from core.reddit_client import RedditClient
from core.browser_reddit_client import BrowserRedditClient
from models.database import Database
from utils.logger import setup_logger
from utils.safety import RateLimiter, ContentSafety

console = Console()
logger = setup_logger("cli")


@click.group()
def cli():
    """Reddit Otomasyon Sistemi"""
    pass


@cli.command()
@click.option('--file', help='Word dosya yolu')
@click.option('--csv', help='CSV dosya yolu (wpblog.csv)')
def parse(file: str, csv: str):
    """Word veya CSV dosyasini parse et ve icerigi veritabanina kaydet"""
    db = Database(str(DB_PATH))
    
    if file:
        console.print(Panel(f"Word dosyasi parse ediliyor: {file}", title="Parse Word"))
        if not Path(file).exists():
            console.print(f"[red]Dosya bulunamadi: {file}[/red]")
            return
        
        parser = WordParser(file)
        if not parser.load():
            console.print("[red]Dosya yuklenemedi[/red]")
            return
        
        content = parser.extract_content()
        analyzer = ContentAnalyzer()
        chunks = analyzer.analyze(content)
        
        for chunk in chunks:
            db.add_post(
                title=chunk.get('title', '')[:100],
                body=chunk.get('content', ''),
                subreddit_type='konusarak_ogren',
                source_content=chunk.get('content', ''),
                source_file=Path(file_path).name
            )
        console.print(f"[green]✓ {len(chunks)} icerik parnasi veritabanina eklendi[/green]")

    elif csv:
        console.print(Panel(f"CSV dosyasi parse ediliyor: {csv}", title="Parse CSV"))
        if not Path(csv).exists():
            console.print(f"[red]Dosya bulunamadi: {csv}[/red]")
            return
            
        parser = CSVParser(csv)
        posts = parser.parse_posts()
        
        for post in posts:
            db.add_post(
                title=post['title'][:100],
                body=post['content'],
                subreddit_type='konusarak_ogren',
                source_content=post['content'],
                source_file=Path(csv).name,
                post_name=post.get('name') # Added post_name support
            )
        console.print(f"[green]✓ {len(posts)} blog yazisi veritabanina eklendi[/green]")
    else:
        console.print("[red]Lutfen --file veya --csv parametresinden birini belirtin.[/red]")


@cli.command()
@click.option('--count', default=1, help='Uretilecek post sayisi')
@click.option('--subreddit', default='both', help='Hedef subreddit: konusarak_ogren, ingilizce_konusma, both')
def generate(count: int, subreddit: str):
    """AI ile Reddit postlari uret"""
    console.print(Panel(f"AI ile {count} post uretiliyor", title="Generate"))
    
    if not NVIDIA_API_KEY:
        console.print("[red]NVIDIA API key bulunamadi. .env dosyasini kontrol edin.[/red]")
        return
    
    ai = AIGenerator(NVIDIA_API_KEY, NVIDIA_API_URL, NVIDIA_MODEL)
    db = Database(str(DB_PATH))
    
    pending_posts = db.get_posts_by_status('pending')
    
    if not pending_posts:
        console.print("[yellow]Islenecek bekleyen post yok. Once parse islemi yapin.[/yellow]")
        return
    
    subreddit_types = ['konusarak_ogren', 'ingilizce_konusma']
    if subreddit != 'both':
        subreddit_types = [subreddit]
    
    generated_count = 0
    for i, post in enumerate(pending_posts[:count]):
        subreddit_type = subreddit_types[i % len(subreddit_types)]
        
        console.print(f"\n[bold]Post {i+1} isleniyor: {post['title']}[/bold]")
        
        # Build the URL if post_name available, else empty
        post_url = ""
        if post.get('post_name'):
            post_url = f"https://www.konusarakogren.com/blog/{post['post_name']}"
        
        result = ai.generate_post(post['title'], post['body'], post_url)
        
        if result['success']:
            db.update_post_status(post['id'], 'generated')
            
            # Save the generated content
            new_id = db.add_post(
                title=result['title'],
                body=result['body'],
                subreddit_type=subreddit_type,
                source_content=post['body'],
                source_file=post.get('source_file'),
                scheduled_for=None,
                post_name=post.get('post_name')
            )
            # Mark the new post as generated so it appears in review
            db.update_post_status(new_id, 'generated')
            
            console.print(f"[green]✓ Reddit Postu uretildi: {result['title']}[/green]")
            generated_count += 1
        else:
            console.print(f"[red]✗ Hata: {result.get('error', 'Bilinmeyen hata')}[/red]")
            db.update_post_status(post['id'], 'error', result.get('error'))
    
    console.print(f"\n[bold green]✓ {generated_count} post basariyla uretildi[/bold green]")


@cli.command()
def review():
    """Postlari manuel olarak incele ve onayla"""
    console.print(Panel("Post Inceleme Modu", title="Review"))
    
    db = Database(str(DB_PATH))
    pending_posts = db.get_posts_by_status('generated')
    
    if not pending_posts:
        console.print("[yellow]Incelenecek post yok[/yellow]")
        return
    
    console.print(f"\nToplam {len(pending_posts)} post bekliyor\n")
    
    for post in pending_posts:
        console.print(Panel(
            f"[bold]Baslik:[/bold] {post['title']}\n\n"
            f"[bold]Icerik:[/bold]\n{post['body'][:500]}{'...' if len(post['body']) > 500 else ''}\n\n"
            f"[dim]Subreddit: {post['subreddit_type']}[/dim]",
            title=f"Post ID: {post['id']}",
            style="blue"
        ))
        
        choice = Prompt.ask(
            "Ne yapalim?",
            choices=["a", "r", "e", "s", "d"],
            default="s"
        )
        
        if choice == "a":
            db.update_post_status(post['id'], 'approved')
            console.print("[green]✓ Onaylandi[/green]")
        elif choice == "r":
            db.update_post_status(post['id'], 'rejected')
            console.print("[red]✗ Reddedildi[/red]")
        elif choice == "e":
            new_title = Prompt.ask("Yeni baslik", default=post['title'][:100])
            console.print(f"[yellow]Baslik guncellendi (manuel duzenleme icin CLI'dan cikin)[/yellow]")
            db.update_post_status(post['id'], 'pending_edit')
        elif choice == "s":
            console.print("[dim]Atlandi[/dim]")
        elif choice == "d":
            if Confirm.ask("Silmek istediginize emin misiniz?"):
                db.delete_post(post['id'])
                console.print("[red]Silindi[/red]")
        
        console.print("-" * 80)


@cli.command()
def post():
    """Onaylanmis postlari Reddit'e gonder"""
    console.print(Panel("Post gonderimi baslatiliyor", title="Post"))
    
    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT]):
        console.print("[red]Reddit API bilgileri eksik. .env dosyasini kontrol edin.[/red]")
        return
    
    reddit = RedditClient(
        REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
        REDDIT_USERNAME, REDDIT_PASSWORD
    )
    
    if not reddit.is_authenticated():
        console.print("[red]Reddit'e baglanti basarisiz[/red]")
        return
    
    db = Database(str(DB_PATH))
    approved_posts = db.get_posts_by_status('approved')
    
    if not approved_posts:
        console.print("[yellow]Gonderilecek onayli post yok[/yellow]")
        return
    
    rate_limiter = RateLimiter(MIN_HOURS_BETWEEN_POSTS)
    
    for post in approved_posts:
        can_post, reason = rate_limiter.can_post()
        
        if not can_post:
            console.print(f"[yellow]{reason} bekleniyor...[/yellow]")
            break
        
        console.print(f"\n[bold]Post gonderiliyor: {post['title']}[/bold]")
        
        result = reddit.post_to_subreddit(
            post['subreddit_type'].replace('_', ''),
            post['title'],
            post['body']
        )
        
        if result['success']:
            db.set_reddit_info(post['id'], result['post_id'], result['post_url'])
            console.print(f"[green]✓ Basarili: {result['post_url']}[/green]")
            rate_limiter.record_post()
        else:
            console.print(f"[red]✗ Hata: {result.get('error')}[/red]")
            db.update_post_status(post['id'], 'error', result.get('error'))
    
    console.print("\n[bold green]✓ Post gonderimi tamamlandi[/bold green]")


@cli.command()
def status():
    """Sistem durumunu goster"""
    console.print(Panel("Sistem Durumu", title="Status"))
    
    db = Database(str(DB_PATH))
    all_posts = db.get_all_posts(limit=10)
    
    table = Table(title="Son Postlar")
    table.add_column("ID", style="cyan")
    table.add_column("Baslik", style="magenta")
    table.add_column("Durum", style="green")
    table.add_column("Tur", style="blue")
    table.add_column("Tarih", style="yellow")
    
    for post in all_posts:
        table.add_row(
            str(post['id']),
            post['title'][:40] + "..." if len(post['title']) > 40 else post['title'],
            post['status'],
            post['subreddit_type'],
            post['created_at'][:16] if post['created_at'] else "N/A"
        )
    
    console.print(table)


@cli.command()
def process_all():
    """Tum Word dosyalarini isle"""
    console.print(Panel("Tum Word dosyalari isleniyor", title="Process All"))
    
    word_files = list(WORD_FILES_DIR.glob("*.docx"))
    
    if not word_files:
        console.print(f"[yellow]{WORD_FILES_DIR} dizininde Word dosyasi bulunamadi[/yellow]")
        return
    
    for file in word_files:
        console.print(f"\n[bold]Isleniyor: {file.name}[/bold]")
        
        parser = WordParser(str(file))
        if parser.load():
            content = parser.extract_content()
            analyzer = ContentAnalyzer()
            chunks = analyzer.analyze(content)
            
            db = Database(str(DB_PATH))
            for chunk in chunks:
                db.add_post(
                    title=chunk.get('title', '')[:100],
                    body=chunk.get('content', ''),
                    subreddit_type='konusarak_ogren',
                    source_content=chunk.get('content', ''),
                    source_file=file.name
                )
            
            console.print(f"[green]✓ {file.name}: {len(chunks)} parca eklendi[/green]")
        else:
            console.print(f"[red]✗ {file.name} yuklenemedi[/red]")
    
    console.print(f"\n[bold green]✓ {len(word_files)} dosya islendi[/bold green]")


@cli.command()
@click.option('--limit', default=DAILY_POST_LIMIT, help='Gonderilecek maksimum post sayisi')
@click.option('--subreddit', default=TARGET_SUBREDDIT, help='Hedef subreddit')
@click.option('--headful', is_flag=True, help='Tarayiciyi gorunur modda ac (ilk giris icin gerekli)')
def browser_post(limit: int, subreddit: str, headful: bool):
    """Onaylanmis postlari tarayici otomasyonu (Playwright) ile gonder"""
    console.print(Panel("Tarayici uzerinden gonderim baslatiliyor", title="Browser Post"))
    
    db = Database(str(DB_PATH))
    approved_posts = db.get_posts_by_status('approved')
    
    if not approved_posts:
        console.print("[yellow]Gonderilecek onayli post yok[/yellow]")
        return
        
    # Check how many posts already posted today
    # Filter by 'posted' status and 'posted_at' date
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM posts WHERE status='posted' AND date(posted_at) = date('now')")
    today_posted_count = cursor.fetchone()[0]
    conn.close()
    
    remaining_limit = limit - today_posted_count
    if remaining_limit <= 0:
        console.print(f"[yellow]Gunluk limit dolmuş ({limit}/{limit}). Yarin tekrar deneriz.[/yellow]")
        return
        
    console.print(f"[cyan]Bugun {today_posted_count} post atildi. {remaining_limit} tane daha atilabilir.[/cyan]")
    
    profile_dir = Path("data/browser_profile")
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    # Force headful for the first time or if requested
    from core.browser_use_client import BrowserUseRedditClient
    client = BrowserUseRedditClient(user_data_dir=str(profile_dir.absolute()))
    
    try:
        posted_count = 0
        for post in approved_posts:
            if posted_count >= remaining_limit:
                break
                
            console.print(f"\n[bold]Post gonderiliyor ({posted_count+1}/{remaining_limit}): {post['title']}[/bold]")
            
            # Subreddit from settings or post or parameter
            target_sub = subreddit or post['subreddit_type'].replace('_', '')
            
            result = client.post_to_subreddit(
                target_sub,
                post['title'],
                post['body']
            )
            
            if result['success']:
                db.set_reddit_info(post['id'], result['post_id'], result['post_url'])
                console.print(f"[green]✓ Basarili: {result['post_url']}[/green]")
                posted_count += 1
                # Wait between posts to be safer
                if posted_count < remaining_limit:
                    sleep_time = 30
                    console.print(f"[dim]{sleep_time} saniye bekleniyor...[/dim]")
                    time.sleep(sleep_time)
            else:
                console.print(f"[red]✗ Hata: {result.get('error')}[/red]")
                if 'screenshot' in result:
                    console.print(f"[dim]Hata goruntusu kaydedildi: {result['screenshot']}[/dim]")
                db.update_post_status(post['id'], 'error', result.get('error'))
                # If it's a structural error might want to stop, 
                # but if it's just one post failing we can continue
                
    finally:
        client.close()
    
    console.print(f"\n[bold green]✓ Toplam {posted_count} post tarayicidan gonderildi.[/bold green]")


if __name__ == '__main__':
    cli()
