(function () {
"strict";

// let slideout = new Slideout({
//   'panel'    : document.querySelector('.wrapper'),
//   'menu'     : document.querySelector('.nav'),
//   'padding'  : 256,
//   'duration' : 0,
//   'tolerance': 10000,
// });

// window.myslideout = slideout

let menuIcon = document.querySelector(".menu-icon")
let navPanel = document.querySelector(".nav")

// slideout.on('beforeopen', () => menuIcon.classList.add("active"))
// slideout.on('beforeclose', () => menuIcon.classList.remove("active"))

// slideout.on('open', (evt) => console.log("open", evt))
// slideout.on('close', (evt) => console.log("close", evt))

let lastInteraction = Date.now()

let navState = {
    isOpen: false,
}

function toggleNav() {
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
      if (Date.now() - lastInteraction > 500) {
          // console.log("tap", evt.type, func.name)
          func(evt)
      }
      lastInteraction = Date.now()
  }
  if ('ontouchstart' in window) {
      node.addEventListener('touchstart', debounced, true)
  } else {
      node.addEventListener('click', debounced)
  }
}

onInteraction(menuIcon, (evt) => {
    // slideout.toggle()
    toggleNav()
    evt.preventDefault()
})


// function closeSlideoutIfLinkClicked(e) {
//     console.log(e.target.closest(".nav"), e.target.closest("a"))
//     if (e.target.closest(".nav") && e.target.closest("a")) {
//         setTimeout(() => {slideout.close();}, 100)
//     }
// }

// onInteraction(document.querySelector(".nav"), closeSlideoutIfLinkClicked)

let contrastIcon = document.querySelector(".toggle-contrast")

onInteraction(contrastIcon, (evt) => {
    lastInteraction = Date.now()
    // console.log("contrast", evt.type, Date.now() / 1000)
    if (document.body.classList.contains("dark")) {
        document.body.classList.remove("dark")
        localStorage.setItem("litprog_theme", "light")
    } else {
        document.body.classList.add("dark")
        localStorage.setItem("litprog_theme", "dark")
    }
    evt.preventDefault()
})

let fallbackTheme = matchMedia('(prefers-color-scheme: dark)').matches ? "dark" : "light"
let selectedTheme = localStorage.getItem("litprog_theme") || fallbackTheme;

if (selectedTheme == "dark") {
    document.body.classList.add("dark")
} else {
    document.body.classList.remove("dark")
}

let pdfIcon = document.querySelector(".pdf-icon")
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
let navigationNodes = document.querySelectorAll(".nav li a")
let setActiveNavTimeout = 0
let activeNavNode = null


function setActiveNav() {
    let wrapperOffset = document.querySelector(".wrapper").offsetTop
    // TODO: Not all nav nodes have headings, so this only works
    //      on the first page. We need to somehow figure out the
    //      number of headings that preceed the active one
    // Oooor, we just stick with a single page ? ¯\_(ツ)_/¯

    // A heading is considered active if it is the first one
    // on screen or the first higher than the middle of the screen
    // (because there may not be a heading on the screen.
    let minActiveY = window.pageYOffset
    let maxActiveY = window.pageYOffset + window.innerHeight / 2
    let headingsOffsetIndex = 0
    for (var i = 0; i < headingNodes.length; i++) {
        let headingNode = headingNodes[i]
        let headingOffset = headingNode.offsetTop + wrapperOffset
        if (headingOffset < minActiveY) {continue}

        let newActiveNav = navigationNodes[i + headingsOffsetIndex]
        // Check if it's below the fold and
        if (i > 0 && headingOffset > maxActiveY) {
          // Use the previous heading
          newActiveNav = navigationNodes[i - 1]
        }

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

function setMenuVis(vis) {
    if (menuNode.classList.contains("offscreen") && vis) {
        headerNode.classList.remove("offscreen")
        menuNode.classList.remove("offscreen")
    } else if (!menuNode.classList.contains("offscreen") && !vis) {
        headerNode.classList.add("offscreen")
        menuNode.classList.add("offscreen")
    }
    prevScrollY = window.pageYOffset
}

let prevScrollY = -1;
setTimeout(function() {prevScrollY = window.pageYOffset}, 1000)

window.addEventListener("scroll", (evt) => {
    clearTimeout(setActiveNavTimeout)
    setActiveNavTimeout = setTimeout(setActiveNav, 100)

    if (Date.now() - lastInteraction < 500) {
        // supress toggle for firefox
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
    lastInteraction = Date.now()
    prevScrollY = window.pageYOffset;
})

let contentNode = document.querySelector(".content")

contentNode.addEventListener('click', (evt) => {
    if (pdfLinks.classList.contains("active") && !evt.target.closest(".pdf-links")) {
        togglePdfLinks()
        evt.preventDefault()
    }
})

function getContentFoldClass(e) {
    let contentRect = contentNode.getBoundingClientRect()
    let deltaContentLeft = Math.abs(e.clientX - contentRect.x)
    // TODO: only return if there's a next chapter
    if (deltaContentLeft < 40) {
        return "lift-fold-left"
    }
    let deltaContentRight = Math.abs(e.clientX - (contentRect.x + contentRect.width))
    if (deltaContentRight < 40) {
        return "lift-fold-right"
    }
    return null
}

let activeTarget = null;
let activePopper = null;
let activePopperNode = null;
let popperDestroyTimeout = null;

function updateContentFoldClass(e) {
    let foldClass = getContentFoldClass(e)
    let altFoldClass = (
        foldClass == "lift-fold-left" ? "lift-fold-right" :
        foldClass == "lift-fold-right" ? "lift-fold-left" :
        null
    )
    let body = document.body
    if (altFoldClass && body.classList.contains(altFoldClass)) {
        body.classList.remove(altFoldClass)
    }
    if (!foldClass) {
        if (body.classList.contains("lift-fold-left")){
            body.classList.remove("lift-fold-left")
        }
        if (body.classList.contains("lift-fold-right")){
            body.classList.remove("lift-fold-right")
        }
    } else if (!body.classList.contains(foldClass)) {
        body.classList.add(foldClass)
    }

}

document.body.addEventListener("mousemove", (e) => {
    let isPopper = !!e.target.closest(".popper")
    if (isPopper) {
        // keep active
        if (popperDestroyTimeout != null) {
            // back on target, cancel destruction
            clearTimeout(popperDestroyTimeout)
            popperDestroyTimeout = null;
        }
        return
    }

    // updateContentFoldClass(e)

    // TODO: More hovers
    //  - Link URL
    //  - Internal link preview (less wrong marks these with °)
    //  - Function definition preview

    let isFnote = e.target.classList.contains("footnote-ref")
    let isAltFnote = isFnote && activeTarget != e.target

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

    let footnoteNum = new RegExp("[0-9]+").exec(e.target.innerText)[0]
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
    activeTarget = e.target
    activePopper = Popper.createPopper(e.target, popperNode, {
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
