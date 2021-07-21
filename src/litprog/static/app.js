(function () {
"strict";

var menuIcon = document.querySelector(".menu-icon")
var sectionsPanel = document.querySelector(".nav-sections")
var chaptersPanel = document.querySelector(".nav-chapters")

var loadingStart = Date.now()
var lastInteraction = Date.now()

var navState = {
    isOpen: false,
}

function toggleNav() {
    lastInteraction = Date.now()
    navState.isOpen = !navState.isOpen
    if (navState.isOpen) {
        sectionsPanel.classList.add("active")
        chaptersPanel.classList.add("active")
        menuIcon.classList.add("active")
    } else {
        sectionsPanel.classList.remove("active")
        chaptersPanel.classList.remove("active")
        menuIcon.classList.remove("active")
    }
}


function onInteraction(node, func) {
  var debounced = function(evt) {
      // console.log("tap", evt.type, func.name, Date.now() - lastInteraction)
      if (Date.now() - lastInteraction > 300) {
          func(evt)
      }
      lastInteraction = Date.now()
  }
  if (0 && 'ontouchstart' in window) {
      // disabled. there might be a benefit to this wrt. interactivity on mobile,
      // but I can't get scrollToTop working right on firefox.
      node.addEventListener('touchstart', debounced, true)
  } else {
      node.addEventListener('click', debounced)
  }
}

onInteraction(menuIcon, (evt) => {
    toggleNav()
    evt.preventDefault()
})


// var scrollTopIcon = document.querySelector(".scroll-to-top")

// onInteraction(scrollTopIcon, (evt) => {
//     lastInteraction = Date.now()
//     window.scroll({top: 0})
//     evt.preventDefault()
// })

function closeNavIfLinkClicked(evt) {
    var navTgt = evt.target.closest(".nav")
    if (!navTgt) return
    var aTgt = evt.target.closest("a")
    if (!aTgt) return
    var headlineId = aTgt.href.split("#")[1]
    var headline = document.querySelector("#" + headlineId)
    if (headline) {
        toggleNav()
        // HACK to supress menu hide effect (as if scrolling)
        // when scrolling is in fact triggered due to navigation
        setMenuVis(true)
        prevScrollY = 99999999
    }
}

onInteraction(document.querySelector(".nav"), closeNavIfLinkClicked)

var contrastIcon = document.querySelector(".toggle-contrast")
var darkOverlay = document.querySelector(".dark-overlay")

onInteraction(contrastIcon, (evt) => {
    lastInteraction = Date.now()
    darkOverlay.style.opacity = "0";
    darkOverlay.style.display = "block";
    setTimeout(function () {
        darkOverlay.style.opacity = "1";
        setTimeout(function () {
            if (document.body.classList.contains("dark")) {
                localStorage.setItem("litprog_theme", "light")
                document.body.classList.remove("dark")
            } else {
                localStorage.setItem("litprog_theme", "dark")
                document.body.classList.add("dark")
            }
            darkOverlay.style.opacity = "0";
            setTimeout(function () {
                darkOverlay.style.display = "none";
            }, 400);
        }, 400);
    }, 20);
    evt.preventDefault()
})

// NOTE (mb 2021-02-25): Each page also has an inline script
var fallbackTheme = matchMedia('(prefers-color-scheme: dark)').matches ? "dark" : "light"
var selectedTheme = localStorage.getItem("litprog_theme") || fallbackTheme;

if (selectedTheme == "dark") {
    document.body.classList.add("dark")
} else {
    document.body.classList.remove("dark")
}

var pdfIcon = document.querySelector(".print-icon")
var pdfLinks = document.querySelector(".pdf-links")
var clickTimetout = -1;

function togglePdfLinks() {
    clearTimeout(clickTimetout)
    if (pdfLinks.classList.contains("active")) {
        pdfLinks.classList.remove("active")
        clickTimetout = setTimeout(() => {pdfLinks.style.display = "none";}, 250)
    } else {
        pdfLinks.style.display = "block";
        clickTimetout = setTimeout(() => {pdfLinks.classList.add("active")}, 50)
    }
}

onInteraction(pdfIcon, togglePdfLinks)

var navScrollerNode = document.querySelector(".nav-scroller")
var sectionsTocNode = document.querySelector(".nav-sections .toc")
var headingNodes = document.querySelectorAll("h1, h2, h3, h4, h5")
var sectionLinkNodes = document.querySelectorAll(".nav-sections a")

var navLinkNodesByHash = {}
for (var i = 0; i < sectionLinkNodes.length; i++) {
    var href = sectionLinkNodes[i].href
    var hrefAnchor = href.slice(href.indexOf("#"))
    navLinkNodesByHash[hrefAnchor] = sectionLinkNodes[i]
}

var setActiveNavTimeout = 0
var activeNavNode = null

function setActiveNav() {
    var wrapperOffset = document.querySelector(".wrapper").offsetTop
    // A heading is considered active if it is the first one
    // on screen or the first higher than the middle of the screen
    // (because there may not be a heading on the screen.
    var minActiveY = window.pageYOffset
    var maxActiveY = window.pageYOffset + window.innerHeight / 2

    for (var i = 0; i < headingNodes.length; i++) {
        var headingNode = headingNodes[i]
        var headingOffset = headingNode.offsetTop + wrapperOffset

        if (headingOffset < minActiveY) {continue}

        if (i == 0 || headingOffset < maxActiveY) {
            var headingHash = "#" + headingNode.getAttribute("id")
        } else {
            // next heading is still below the fold, so use the previous one
            var headingHash = "#" + headingNodes[i - 1].getAttribute("id")
        }

        var newActiveNav = navLinkNodesByHash[headingHash];
        if (!newActiveNav) {return}

        if (activeNavNode == newActiveNav) {return}

        if (activeNavNode) {
            activeNavNode.classList.remove("active")
        }
        activeNavNode = newActiveNav
        newActiveNav.classList.add("active")

        var relOffsetTop = newActiveNav.offsetTop - sectionsTocNode.offsetTop
        var scrollTop = navScrollerNode.scrollTop
        var scrollBottom = scrollTop + 2 * navScrollerNode.offsetHeight / 3
        if (!(scrollTop < relOffsetTop && relOffsetTop < scrollBottom)) {
            var navTop = Math.max(0, relOffsetTop - navScrollerNode.offsetHeight / 2)
            navScrollerNode.scrollTop = navTop;
        }
        break
    }
    if (activeNavNode) {
        var sectionLinkNodes = document.querySelectorAll(".nav-sections a")
        var isAfterActive = false
        for (var i = 0; i < sectionLinkNodes.length; i++) {
            var navLinkNode = sectionLinkNodes[i];
            if (navLinkNode === activeNavNode) {
                isAfterActive = true;
            }
            if (isAfterActive) {
                navLinkNode.classList.remove("blur")
            } else {
                navLinkNode.classList.add("blur")
            }
        }
    }
}

setActiveNav()

var headerNode = document.querySelector(".header")
var menuNode = document.querySelector(".menu")

var prevScrollY = -1;
setTimeout(function() {prevScrollY = window.pageYOffset}, 1000)

function setMenuVis(vis) {
    lastInteraction = Date.now()
    prevScrollY = window.pageYOffset
    if (menuNode.classList.contains("offscreen") && vis) {
        headerNode.classList.remove("offscreen")
        menuNode.classList.remove("offscreen")
    } else if (!menuNode.classList.contains("offscreen") && !vis) {
        headerNode.classList.add("offscreen")
        menuNode.classList.add("offscreen")
    } else {
        return
    }
}

var contentNode = document.querySelector(".content")

contentNode.addEventListener('click', (evt) => {
    if (pdfLinks.classList.contains("active") && !evt.target.closest(".pdf-links")) {
        togglePdfLinks()
        evt.preventDefault()
    }
})

window.addEventListener("scroll", (evt) => {
    clearTimeout(setActiveNavTimeout)
    setActiveNavTimeout = setTimeout(setActiveNav, 100)
    if (window.pageYOffset < 10) {
        setMenuVis(true)
        return
    }

    if (window.pageYOffset > contentNode.offsetHeight - window.innerHeight) {
        setMenuVis(true)
        return
    }

    if (Date.now() - lastInteraction < 700) {
        // supress toggle for firefox
        return
    }

    if (Date.now() - loadingStart < 2000) {
        // supress nav toggle due to initial page reflow
        setMenuVis(true)
        return
    }

    // if deltaY is positive then we're scrolling down
    var deltaY = window.pageYOffset - prevScrollY
    var hasScrolledUp = deltaY < -20 || window.pageYOffset == 0
    var hasScrolledDown = deltaY > 50
    if (hasScrolledUp) setMenuVis(true)
    if (hasScrolledDown) setMenuVis(false)

    // if (navState.isOpen) {
    //     toggleNav();
    //     headerNode.classList.add("offscreen")
    //     menuNode.classList.add("offscreen")
    //     return
    // }

    setMenuVis(window.pageYOffset < 10 || deltaY < 0)
})

var activeTarget = null;
var activePopper = null;
var activePopperNode = null;
var popperDestroyTimeout = null;

document.body.addEventListener("mousemove", (evt) => {
    if (evt.target.nodeName == "#text") {
        return
    }

    var isPopper = !!evt.target.closest(".popper")
    if (isPopper) {
        // keep active
        if (popperDestroyTimeout != null) {
            // back on target, cancel destruction
            clearTimeout(popperDestroyTimeout)
            popperDestroyTimeout = null;
        }
        return
    }

    // TODO: More hovers
    //  - Link URL
    //  - Internal link preview (less wrong marks these with °)
    //  - Function definition preview

    var isFnote = evt.target.classList.contains("footnote-ref")
    var isAltFnote = isFnote && activeTarget != evt.target

    if (!isFnote || isAltFnote) {
        // hide the current popper
        if (activePopper && (isAltFnote || popperDestroyTimeout == null)) {
            var popperDestroyer = ((popper, popperNode) => () => {
                var popperCleanup = () => {
                    popper.destroy()
                    document.body.removeChild(popperNode)
                }

                setTimeout(popperCleanup, 300)
                popperNode.style.opacity = "0"
                if (popperNode == activePopperNode) {
                    activeTarget = null
                    activePopper = null
                    activePopperNode = null
                    popperDestroyTimeout = null
                }
            })(activePopper, activePopperNode)

            if (isAltFnote) {
                clearTimeout(popperDestroyTimeout)
                popperDestroyer()
            } else {
                popperDestroyTimeout = setTimeout(popperDestroyer, 500)
            }
        }
        if (!isFnote) {
            return
        }
    }

    if (activePopper) {
        // popper already created
        return
    }

    var footnoteNum = new RegExp("[0-9]+").exec(evt.target.innerText)[0]
    var footnoteNode = document.querySelector(`.footnote > ol > li:nth-child(${footnoteNum})`)
    var popperNode = document.createElement("div")
    popperNode.setAttribute("footnote-number", footnoteNum)
    popperNode.classList.add("popper")
    popperNode.innerHTML = (
        '<div class="arrow" data-popper-arrow></div><div class="popper-wrap">'
        + footnoteNode.innerHTML
        + '</div>'
    )
    document.body.appendChild(popperNode)
    activeTarget = evt.target
    activePopper = Popper.createPopper(evt.target, popperNode, {
        placement: 'top',
        modifiers: [
            {
                name: 'offset',
                options: {offset: [0, 20]},
            },
            {
                name: 'preventOverflow',
                options: {padding: 25},
            },
        ],
    });
    activePopperNode = popperNode
    setTimeout(() => {activePopperNode.style.opacity = "1"}, 10)
})

})();
