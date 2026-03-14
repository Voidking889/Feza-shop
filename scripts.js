
const products = [
            {
                id: 1,
                name: "Premium Headphones",
                price: 89.99,
                originalPrice: null,
                rating: 5,
                image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=450&h=300&fit=crop",
                onSale: false
            },
            {
                id: 2,
                name: "Wireless Speaker",
                price: 49.99,
                originalPrice: 79.99,
                rating: 5,
                image: "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=450&h=300&fit=crop",
                onSale: true
            },
            {
                id: 3,
                name: "Smart Watch",
                price: 199.99,
                originalPrice: 299.99,
                rating: 4,
                image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=450&h=300&fit=crop",
                onSale: true
            },
            {
                id: 4,
                name: "Laptop Stand",
                price: 39.99,
                originalPrice: null,
                rating: 5,
                image: "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=450&h=300&fit=crop",
                onSale: false
            },
            {
                id: 5,
                name: "Gaming Mouse",
                price: 24.99,
                originalPrice: 49.99,
                rating: 4,
                image: "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=450&h=300&fit=crop",
                onSale: true
            },
            {
                id: 6,
                name: "Mechanical Keyboard",
                price: 129.99,
                originalPrice: null,
                rating: 5,
                image: "https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=450&h=300&fit=crop",
                onSale: false
            },
            {
                id: 7,
                name: "Phone Case",
                price: 19.99,
                originalPrice: 29.99,
                rating: 4,
                image: "https://images.unsplash.com/photo-1556656793-08538906a9f8?w=450&h=300&fit=crop",
                onSale: true
            },
            {
                id: 8,
                name: "Tablet Holder",
                price: 34.99,
                originalPrice: null,
                rating: 5,
                image: "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=450&h=300&fit=crop",
                onSale: false
            }
        ];

        // Cart functionality
        let cart = [];

        // DOM elements
        const loadingOverlay = document.getElementById('loadingOverlay');
        const productsContainer = document.getElementById('productsContainer');
        const cartCount = document.getElementById('cartCount');
        const cartItems = document.getElementById('cartItems');
        const cartTotal = document.getElementById('cartTotal');
        const notification = document.getElementById('notification');
        const notificationText = document.getElementById('notificationText');
        const checkoutBtn = document.getElementById('checkoutBtn');

        // Initialize app
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                loadingOverlay.style.opacity = '0';
                setTimeout(() => {
                    loadingOverlay.style.display = 'none';
                    renderProducts();
                    animateCards();
                }, 500);
            }, 1500);
        });

        // Render products
        function renderProducts() {
            productsContainer.innerHTML = products.map(product => `
                <div class="col mb-5">
                    <div class="card product-card h-100">
                        <div class="product-image">
                            ${product.onSale ? '<div class="sale-badge">Sale</div>' : ''}
                            <img src="${product.image}" alt="${product.name}" />
                        </div>
                        <div class="card-body product-info">
                            <h5 class="product-name">${product.name}</h5>
                            <div class="product-rating mb-2">
                                <div class="star-rating">
                                    ${'★'.repeat(product.rating)}${'☆'.repeat(5 - product.rating)}
                                </div>
                            </div>
                            <div class="product-price">
                                ${product.originalPrice ? `<span class="price-original">$${product.originalPrice}</span>` : ''}
                                <span class="price-sale">$${product.price}</span>
                            </div>
                        </div>
                        <div class="card-footer bg-transparent border-0 pb-4">
                            <div class="text-center">
                                <button class="btn add-to-cart-btn" onclick="addToCart(${product.id})">
                                    <span><i class="bi-cart-plus me-2"></i>Add to Cart</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        // Animate cards
        function animateCards() {
            const cards = document.querySelectorAll('.product-card');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.classList.add('animate-in');
                }, index * 150);
            });
        }

        // Add to cart function
        function addToCart(productId) {
            const product = products.find(p => p.id === productId);
            const existingItem = cart.find(item => item.id === productId);

            if (existingItem) {
                existingItem.quantity += 1;
            } else {
                cart.push({...product, quantity: 1});
            }

            updateCartUI();
            showNotification(`${product.name} added to cart!`);
        }

        // Update cart UI
        function updateCartUI() {
            // Update cart count
            const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
            cartCount.textContent = totalItems;

            // Update cart items
            if (cart.length === 0) {
                cartItems.innerHTML = '<p class="text-center text-muted">Your cart is empty</p>';
            } else {
                cartItems.innerHTML = cart.map(item => `
                    <div class="cart-item">
                        <div class="row align-items-center">
                            <div class="col-3">
                                <img src="${item.image}" alt="${item.name}" class="img-fluid rounded" style="height: 60px; object-fit: cover;">
                            </div>
                            <div class="col-6">
                                <h6 class="mb-1">${item.name}</h6>
                                <small class="text-muted">$${item.price} each</small>
                            </div>
                            <div class="col-3 text-end">
                                <div class="d-flex align-items-center justify-content-end">
                                    <button class="btn btn-sm btn-outline-secondary me-1" onclick="changeQuantity(${item.id}, -1)">-</button>
                                    <span class="mx-2">${item.quantity}</span>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="changeQuantity(${item.id}, 1)">+</button>
                                </div>
                                <button class="btn btn-sm text-danger mt-1" onclick="removeFromCart(${item.id})">
                                    <i class="bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('');
            }

            // Update total
            const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            cartTotal.textContent = total.toFixed(2);
        }

        // Change quantity
        function changeQuantity(productId, change) {
            const item = cart.find(item => item.id === productId);
            if (item) {
                item.quantity += change;
                if (item.quantity <= 0) {
                    removeFromCart(productId);
                } else {
                    updateCartUI();
                }
            }
        }

        // Remove from cart
        function removeFromCart(productId) {
            cart = cart.filter(item => item.id !== productId);
            updateCartUI();
            showNotification('Item removed from cart');
        }

        // Show notification
        function showNotification(message) {
            notificationText.textContent = message;
            notification.classList.add('show');
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }

        // Checkout function
        checkoutBtn.addEventListener('click', function() {
            if (cart.length === 0) {
                alert('Your cart is empty!');
                return;
            }
            
            alert('Thank you for shopping with Feza Shop! Your order has been placed.');
            cart = [];
            updateCartUI();
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('cartModal'));
            modal.hide();
        });

        // Smooth scrolling for navbar links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            });
        });

        // Navbar background change on scroll
        window.addEventListener('scroll', function() {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 50) {
                navbar.style.background = 'rgba(26, 26, 26, 0.95)';
                navbar.style.backdropFilter = 'blur(10px)';
            } else {
                navbar.style.background = 'var(--primary-black)';
                navbar.style.backdropFilter = 'none';
            }
        });