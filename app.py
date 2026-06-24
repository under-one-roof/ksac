from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from config import Config
from supabase import create_client, Client
import os

app = Flask(__name__)
app.config.from_object(Config)

# Init Supabase
supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Context Processor for Dark Mode
@app.context_processor
def inject_globals():
    return {
        'dark_mode': session.get('dark_mode', True),
        'is_logged_in': 'user' in session
    }

# --- PUBLIC ROUTES ---

@app.route('/')
def index():
    # Ambil data dari Supabase
    products_res = supabase.table('products').select('*, categories(name)').limit(8).execute()
    testimonials_res = supabase.table('testimonials').select('*').execute()
    gallery_res = supabase.table('gallery').select('*').limit(6).execute()
    
    return render_template('index.html', 
                           products=products_res.data, 
                           testimonials=testimonials_res.data,
                           galleries=gallery_res.data)

@app.route('/toggle_theme')
def toggle_theme():
    session['dark_mode'] = not session.get('dark_mode', True)
    return redirect(request.referrer or url_for('index'))

@app.route('/category/<slug>')
def category(slug):
    # Ubah slug menjadi format Title Case (e.g., 'furniture' -> 'Furniture', 't-shirt' -> 'T-Shirt')
    # Python method .title() otomatis mengkapitalisasi huruf setelah tanda hubung
    category_name = slug.title()
    
    # 1. Cari ID kategori berdasarkan nama kategori terlebih dahulu
    cat_res = supabase.table('categories').select('id').eq('name', category_name).execute()
    
    # Jika kategori tidak ditemukan di database
    if not cat_res.data:
        return render_template('category.html', category_name=category_name, slug=slug, products=[])
        
    category_id = cat_res.data[0]['id']
    
    # 2. Ambil produk HANYA berdasarkan category_id tersebut
    products_res = supabase.table('products').select('*').eq('category_id', category_id).execute()
    
    return render_template('category.html', 
                           category_name=category_name, 
                           slug=slug, 
                           products=products_res.data)
    
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/gallery')
def gallery():
    gallery_res = supabase.table('gallery').select('*').execute()
    return render_template('gallery.html', galleries=gallery_res.data)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'whatsapp': request.form.get('whatsapp'),
            'message': request.form.get('message')
        }
        # Insert ke Supabase
        supabase.table('contact_messages').insert(data).execute()
        flash('Pesan Anda berhasil dikirim!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

# --- ADMIN ROUTES ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            # Cek user di Supabase
            user_res = supabase.table('users').select('*').eq('username', username).execute()
            
            # PRINT HASIL DARI SUPABASE DI TERMINAL
            print("Hasil query Supabase:", user_res.data) 
            
            if user_res.data and len(user_res.data) > 0:
                user_data = user_res.data[0]
                if user_data['password_hash'] == password:
                    session['user'] = user_data
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Password salah!', 'danger')
            else:
                flash('Username tidak ditemukan!', 'danger')
                
        except Exception as e:
            print("Error Supabase:", e)
            flash('Terjadi kesalahan sistem.', 'danger')
            
    return render_template('admin/login.html')

@app.route('/admin')
def admin_dashboard():
    if 'user' not in session:
        return redirect(url_for('admin_login'))
    
    # Fetch counts for dashboard
    products_count = len(supabase.table('products').select('id').execute().data)
    categories_count = len(supabase.table('categories').select('id').execute().data)
    messages_count = len(supabase.table('contact_messages').select('id').execute().data)
    
    return render_template('admin/dashboard.html', 
                           products_count=products_count,
                           categories_count=categories_count,
                           messages_count=messages_count)
    

@app.route('/admin/logout')
def admin_logout():
    session.pop('user', None)
    # Mengarahkan kembali ke halaman utama (home)
    return redirect(url_for('index'))

#if __name__ == '__main__':
 #   app.run(debug=True)
 
 
 # --- FUNGSI TAMBAHAN UNTUK ADMIN PANEL ---

@app.route('/admin/messages')
def admin_messages():
    if 'user' not in session:
        return redirect(url_for('admin_login'))
    messages_res = supabase.table('contact_messages').select('*').order('created_at', desc=True).execute()
    return render_template('admin/messages.html', messages=messages_res.data)

@app.route('/admin/products')
def admin_products():
    if 'user' not in session:
        return redirect(url_for('admin_login'))
    products_res = supabase.table('products').select('*, categories(name)').order('created_at', desc=True).execute()
    categories_res = supabase.table('categories').select('*').execute()
    return render_template('admin/products.html', products=products_res.data, categories=categories_res.data)

@app.route('/admin/products/add', methods=['POST'])
def admin_add_product():
    if 'user' not in session:
        return redirect(url_for('admin_login'))
    
    # Ambil data dari form
    name = request.form.get('name')
    price = request.form.get('price')
    category_id = request.form.get('category_id')
    description = request.form.get('description')
    image_url = request.form.get('image_url') # Untuk demo, kita input URL gambar langsung
    
    data = {
        'name': name,
        'price': float(price),
        'category_id': int(category_id),
        'description': description,
        'image_url': image_url
    }
    
    # Insert ke Supabase
    supabase.table('products').insert(data).execute()
    flash('Produk berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/delete/<int:product_id>')
def admin_delete_product(product_id):
    if 'user' not in session:
        return redirect(url_for('admin_login'))
    
    supabase.table('products').delete().eq('id', product_id).execute()
    flash('Produk berhasil dihapus!', 'success')
    return redirect(url_for('admin_products'))

# --- KATEGORI MANAGEMENT ---
@app.route('/admin/categories', methods=['GET', 'POST'])
def admin_categories():
    if 'user' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        supabase.table('categories').insert({'name': name}).execute()
        flash('Kategori berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_categories'))
        
    categories_res = supabase.table('categories').select('*').order('name', desc=False).execute()
    return render_template('admin/categories.html', categories=categories_res.data)

@app.route('/admin/categories/delete/<int:cat_id>')
def admin_delete_category(cat_id):
    if 'user' not in session:
        return redirect(url_for('admin_login'))
    supabase.table('categories').delete().eq('id', cat_id).execute()
    flash('Kategori dihapus!', 'success')
    return redirect(url_for('admin_categories'))

# --- GALLERY MANAGEMENT ---
@app.route('/admin/gallery', methods=['GET', 'POST'])
def admin_gallery():
    if 'user' not in session:
        return redirect(url_for('admin_login'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('image_url')
        supabase.table('gallery').insert({'title': title, 'image_url': image_url}).execute()
        flash('Gambar galeri ditambahkan!', 'success')
        return redirect(url_for('admin_gallery'))
        
    gallery_res = supabase.table('gallery').select('*').order('id', desc=True).execute()
    return render_template('admin/gallery.html', galleries=gallery_res.data)

@app.route('/admin/gallery/delete/<int:gal_id>')
def admin_delete_gallery(gal_id):
    if 'user' not in session:
        return redirect(url_for('admin_login'))
    supabase.table('gallery').delete().eq('id', gal_id).execute()
    flash('Gambar dihapus!', 'success')
    return redirect(url_for('admin_gallery'))

# --- TESTIMONIALS MANAGEMENT ---
@app.route('/admin/testimonials', methods=['GET', 'POST'])
def admin_testimonials():
    if 'user' not in session:
        return redirect(url_for('admin_login'))
        
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        message = request.form.get('message')
        supabase.table('testimonials').insert({'customer_name': customer_name, 'message': message}).execute()
        flash('Testimoni ditambahkan!', 'success')
        return redirect(url_for('admin_testimonials'))
        
    testi_res = supabase.table('testimonials').select('*').order('id', desc=True).execute()
    return render_template('admin/testimonials.html', testimonials=testi_res.data)

@app.route('/admin/testimonials/delete/<int:testi_id>')
def admin_delete_testimonial(testi_id):
    if 'user' not in session:
        return redirect(url_for('admin_login'))
    supabase.table('testimonials').delete().eq('id', testi_id).execute()
    flash('Testimoni dihapus!', 'success')
    return redirect(url_for('admin_testimonials'))

# --- USERS MANAGEMENT ---
@app.route('/admin/users')
def admin_users():
    if 'user' not in session:
        return redirect(url_for('admin_login'))
        
    users_res = supabase.table('users').select('*').order('id', desc=False).execute()
    return render_template('admin/users.html', users=users_res.data)

# --- SETTINGS (Static Page) ---
@app.route('/admin/settings')
def admin_settings():
    if 'user' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin/settings.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6006, debug=True)