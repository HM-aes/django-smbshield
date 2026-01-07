/**
 * SMBShield - GSAP Animations
 * Scroll-triggered animations for the cybersecurity education platform
 */

// Register ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

// Initialize animations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initScrollAnimations();
    initHoverAnimations();
});

/**
 * Initialize scroll-triggered animations
 */
function initScrollAnimations() {
    // Fade up animations
    gsap.utils.toArray('.fade-up').forEach((element, i) => {
        const delay = element.dataset.delay || 0;

        gsap.fromTo(element,
            {
                opacity: 0,
                y: 30
            },
            {
                opacity: 1,
                y: 0,
                duration: 0.8,
                delay: parseFloat(delay),
                ease: 'power2.out',
                scrollTrigger: {
                    trigger: element,
                    start: 'top 85%',
                    toggleActions: 'play none none none'
                },
                onComplete: () => element.classList.add('animated')
            }
        );
    });

    // Slide left animations
    gsap.utils.toArray('.slide-left').forEach((element, i) => {
        const delay = element.dataset.delay || 0;

        gsap.fromTo(element,
            {
                opacity: 0,
                x: -30
            },
            {
                opacity: 1,
                x: 0,
                duration: 0.8,
                delay: parseFloat(delay),
                ease: 'power2.out',
                scrollTrigger: {
                    trigger: element,
                    start: 'top 85%',
                    toggleActions: 'play none none none'
                },
                onComplete: () => element.classList.add('animated')
            }
        );
    });

    // Scale in animations
    gsap.utils.toArray('.scale-in').forEach((element, i) => {
        const delay = element.dataset.delay || 0;

        gsap.fromTo(element,
            {
                opacity: 0,
                scale: 0.9
            },
            {
                opacity: 1,
                scale: 1,
                duration: 0.6,
                delay: parseFloat(delay),
                ease: 'back.out(1.7)',
                scrollTrigger: {
                    trigger: element,
                    start: 'top 85%',
                    toggleActions: 'play none none none'
                },
                onComplete: () => element.classList.add('animated')
            }
        );
    });

    // Stagger animations for lists
    gsap.utils.toArray('.stagger-children').forEach((container) => {
        const children = container.children;

        gsap.fromTo(children,
            {
                opacity: 0,
                y: 20
            },
            {
                opacity: 1,
                y: 0,
                duration: 0.5,
                stagger: 0.1,
                ease: 'power2.out',
                scrollTrigger: {
                    trigger: container,
                    start: 'top 85%',
                    toggleActions: 'play none none none'
                }
            }
        );
    });
}

/**
 * Initialize hover animations
 */
function initHoverAnimations() {
    // Card hover effects
    document.querySelectorAll('.card-hover').forEach((card) => {
        card.addEventListener('mouseenter', () => {
            gsap.to(card, {
                y: -5,
                boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3)',
                duration: 0.3,
                ease: 'power2.out'
            });
        });

        card.addEventListener('mouseleave', () => {
            gsap.to(card, {
                y: 0,
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                duration: 0.3,
                ease: 'power2.out'
            });
        });
    });

    // Button pulse effect
    document.querySelectorAll('.btn-pulse').forEach((btn) => {
        btn.addEventListener('mouseenter', () => {
            gsap.to(btn, {
                scale: 1.05,
                duration: 0.2,
                ease: 'power2.out'
            });
        });

        btn.addEventListener('mouseleave', () => {
            gsap.to(btn, {
                scale: 1,
                duration: 0.2,
                ease: 'power2.out'
            });
        });
    });
}

/**
 * Utility: Animate element on demand
 */
function animateElement(element, animation = 'fadeUp') {
    const animations = {
        fadeUp: { from: { opacity: 0, y: 30 }, to: { opacity: 1, y: 0 } },
        fadeDown: { from: { opacity: 0, y: -30 }, to: { opacity: 1, y: 0 } },
        fadeLeft: { from: { opacity: 0, x: -30 }, to: { opacity: 1, x: 0 } },
        fadeRight: { from: { opacity: 0, x: 30 }, to: { opacity: 1, x: 0 } },
        scaleIn: { from: { opacity: 0, scale: 0.8 }, to: { opacity: 1, scale: 1 } },
        bounce: { from: { y: 0 }, to: { y: -10, yoyo: true, repeat: 1 } }
    };

    const anim = animations[animation] || animations.fadeUp;

    gsap.fromTo(element, anim.from, {
        ...anim.to,
        duration: 0.6,
        ease: 'power2.out'
    });
}

// Export for use in other scripts
window.SMBShield = window.SMBShield || {};
window.SMBShield.animate = animateElement;
