(function () {
"strict";

let menuIcon = document.querySelector(".menu-icon")
let navPanel = document.querySelector(".nav")

let loadingStart = Date.now()
let lastInteraction = Date.now()

let navState = {
    isOpen: false,
}

function toggleNav() {
    lastInteraction = Date.now()
    navState.isOpen = !navState.isOpen
    if (navState.isOpen) {
        navPanel.classList.add("active")
        menuIcon.classList.add("active")
    } else {
        navPanel.classList.remove("active")
        menuIcon.classList.remove("active")
    }
}


function onInteraction(node, func) {
  const debounced = function(evt) {
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


let scrollTopIcon = document.querySelector(".scroll-to-top")

onInteraction(scrollTopIcon, (evt) => {
    lastInteraction = Date.now()
    window.scroll({top: 0})
    evt.preventDefault()
})

function closeNavIfLinkClicked(evt) {
    let navTgt = evt.target.closest(".nav")
    if (!navTgt) return
    let aTgt = evt.target.closest("a")
    if (!aTgt) return
    let headlineId = aTgt.href.split("#")[1]
    let headline = document.querySelector("#" + headlineId)
    if (headline) {
        toggleNav()
        // HACK to supress menu hide effect (as if scrolling)
        // when scrolling is in fact triggered due to navigation
        setMenuVis(true)
        prevScrollY = 99999999
    }
}

onInteraction(document.querySelector(".nav"), closeNavIfLinkClicked)

let contrastIcon = document.querySelector(".toggle-contrast")
let darkOverlay = document.querySelector(".dark-overlay")

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
            }, 350);
        }, 350);
    }, 20);
    evt.preventDefault()
})

let fallbackTheme = matchMedia('(prefers-color-scheme: dark)').matches ? "dark" : "light"
let selectedTheme = localStorage.getItem("litprog_theme") || fallbackTheme;

if (selectedTheme == "dark") {
    document.body.classList.add("dark")
} else {
    document.body.classList.remove("dark")
}

let pdfIcon = document.querySelector(".print-icon")
let pdfLinks = document.querySelector(".pdf-links")
let clickTimetout = -1;

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

let navScrollerNode = document.querySelector(".nav-scroller")
let tocNode = document.querySelector(".toc")
let headingNodes = document.querySelectorAll("h1, h2, h3, h4, h5")
let navLinkNodes = document.querySelectorAll(".toc a")

let navLinkNodesByHash = {}
for (var i = 0; i < navLinkNodes.length; i++) {
    let href = navLinkNodes[i].href
    let hrefAnchor = href.slice(href.indexOf("#"))
    navLinkNodesByHash[hrefAnchor] = navLinkNodes[i]
}

let setActiveNavTimeout = 0
let activeNavNode = null

function setActiveNav() {
    let wrapperOffset = document.querySelector(".wrapper").offsetTop
    // A heading is considered active if it is the first one
    // on screen or the first higher than the middle of the screen
    // (because there may not be a heading on the screen.
    let minActiveY = window.pageYOffset
    let maxActiveY = window.pageYOffset + window.innerHeight / 2

    for (var i = 0; i < headingNodes.length; i++) {
        let headingNode = headingNodes[i]
        let headingOffset = headingNode.offsetTop + wrapperOffset

        if (headingOffset < minActiveY) {continue}

        if (i == 0 || headingOffset < maxActiveY) {
            var headingHash = "#" + headingNode.getAttribute("id")
        } else {
            // next heading is still below the fold, so use the previous one
            var headingHash = "#" + headingNodes[i - 1].getAttribute("id")
        }

        let newActiveNav = navLinkNodesByHash[headingHash];

        if (activeNavNode == newActiveNav) {return}

        if (activeNavNode) {
            activeNavNode.classList.remove("active")
        }
        activeNavNode = newActiveNav
        newActiveNav.classList.add("active")

        let relOffsetTop = newActiveNav.offsetTop - tocNode.offsetTop
        let scrollTop = navScrollerNode.scrollTop
        let scrollBottom = scrollTop + 2 * navScrollerNode.offsetHeight / 3
        if (!(scrollTop < relOffsetTop && relOffsetTop < scrollBottom)) {
            navScrollerNode.scrollTop = Math.max(0, relOffsetTop - navScrollerNode.offsetHeight / 2)
        }
        break
    }
}

setActiveNav()

let headerNode = document.querySelector(".header")
let menuNode = document.querySelector(".menu")

let prevScrollY = -1;
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

window.addEventListener("scroll", (evt) => {
    clearTimeout(setActiveNavTimeout)
    setActiveNavTimeout = setTimeout(setActiveNav, 100)
    if (window.pageYOffset < 10) {
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
    let deltaY = window.pageYOffset - prevScrollY
    let hasScrolledUp = deltaY < -20 || window.pageYOffset == 0
    let hasScrolledDown = deltaY > 50
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

let contentNode = document.querySelector(".content")

contentNode.addEventListener('click', (evt) => {
    if (pdfLinks.classList.contains("active") && !evt.target.closest(".pdf-links")) {
        togglePdfLinks()
        evt.preventDefault()
    }
})

let activeTarget = null;
let activePopper = null;
let activePopperNode = null;
let popperDestroyTimeout = null;

document.body.addEventListener("mousemove", (evt) => {
    if (evt.target.nodeName == "#text") {
        return
    }

    let isPopper = !!evt.target.closest(".popper")
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

    let isFnote = evt.target.classList.contains("footnote-ref")
    let isAltFnote = isFnote && activeTarget != evt.target

    if (!isFnote || isAltFnote) {
        // hide the current popper
        if (activePopper && (isAltFnote || popperDestroyTimeout == null)) {
            let popperDestroyer = ((popper, popperNode) => () => {
                let popperCleanup = () => {
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

    let footnoteNum = new RegExp("[0-9]+").exec(evt.target.innerText)[0]
    let footnoteNode = document.querySelector(`.footnote > ol > li:nth-child(${footnoteNum})`)
    let popperNode = document.createElement("div")
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
