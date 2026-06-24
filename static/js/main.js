// Initialize AOS
AOS.init({
    duration: 1000,
    once: true,
    offset: 100
});

// GSAP Floating Elements Animation
if (window.gsap) {
    gsap.to(".el-1", { y: 30, rotation: 360, duration: 6, repeat: -1, yoyo: true, ease: "sine.inOut" });
    gsap.to(".el-2", { y: -40, rotation: -360, duration: 8, repeat: -1, yoyo: true, ease: "sine.inOut" });
}

// Counter Animation
function animateCounter(id, target) {
    const obj = document.getElementById(id);
    if(!obj) return;
    let count = 0;
    const increment = target / 100;
    const updateCount = () => {
        if(count < target) {
            count += increment;
            obj.innerText = Math.ceil(count);
            setTimeout(updateCount, 20);
        } else {
            obj.innerText = target + (target > 100 ? '+' : '');
        }
    };
    updateCount();
}

// Run counters when in view
const counters = document.querySelectorAll('.counter');
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if(entry.isIntersecting) {
            const target = +entry.target.getAttribute('data-target');
            animateCounter(entry.target.id, target);
            observer.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });
counters.forEach(c => observer.observe(c));

// Live Search & Filter (Category Page)
 $(document).ready(function() {
    $("#searchInput").on("keyup", function() {
        var value = $(this).val().toLowerCase();
        $(".product-item").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });

    // Price Filter Logic
    $("#priceRange").on("input", function() {
        var maxPrice = parseInt($(this).val());
        $("#priceValue").text(maxPrice.toLocaleString('id-ID'));
        
        $(".product-item").each(function() {
            var price = parseInt($(this).find(".price-tag").data("price"));
            if (price <= maxPrice) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });
});