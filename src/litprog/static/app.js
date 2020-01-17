(function () {
"strict";

let slideout = new Slideout({
  'panel': document.querySelector('.wrapper'),
  'menu': document.querySelector('.nav'),
  'padding': 256,
  'duration': 250,
  'tolerance': 100,
});

slideout.on('beforeopen', () => menuIcon.classList.add("active"))
slideout.on('beforeclose', () => menuIcon.classList.remove("active"))

function onInteraction(node, func) {
  let lastClick = 0
  const debounced = function(evt) {
      if (Date.now() - lastClick > 250) {func(evt)}
      lastClick = Date.now()
  }
  node.addEventListener('mousedown', debounced)
  node.addEventListener('touchstart', debounced)
}

let menuIcon = document.querySelector(".menu-icon")
onInteraction(menuIcon, () => slideout.toggle())


// function closeSlideoutIfLinkClicked(e) {
//     console.log(e.target.closest(".nav"), e.target.closest("a"))
//     if (e.target.closest(".nav") && e.target.closest("a")) {
//         setTimeout(() => {slideout.close();}, 100)
//     }
// }

// onInteraction(document.querySelector(".nav"), closeSlideoutIfLinkClicked)

let contrastIcon = document.querySelector(".toggle-contrast")
onInteraction(contrastIcon, function () {
  if (document.body.classList.contains("dark")) {
      document.body.classList.remove("dark")
      localStorage.setItem("litprog_theme", "light")
  } else {
      document.body.classList.add("dark")
      localStorage.setItem("litprog_theme", "dark")
  }
})

let fallbackTheme = matchMedia('(prefers-color-scheme: dark)').matches ? "dark" : "light"
let selectedTheme = localStorage.getItem("litprog_theme") || fallbackTheme;

if (selectedTheme == "dark") {
    document.body.classList.add("dark")
} else {
    document.body.classList.remove("dark")
}

let printIcon = document.querySelector(".print-icon")
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

onInteraction(printIcon, togglePdfLinks)

let headerNode = document.querySelector(".header")
let prevScrollY = -1;
let anchorY = -1;

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
    // Oooor, we just stick with a single page ?

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

window.addEventListener("scroll", (e) => {
    clearTimeout(setActiveNavTimeout)
    setActiveNavTimeout = setTimeout(setActiveNav, 150)

    if (prevScrollY < 0 || slideout.isOpen()) {
        slideout.close()
        prevScrollY = window.pageYOffset;
        anchorY = window.pageYOffset;
        headerNode.style.marginTop = "0px";
        return
    }

    let deltaY = window.pageYOffset - prevScrollY
    prevScrollY = window.pageYOffset;

    let headerHeight = headerNode.clientHeight
    if (deltaY < 0) {
        anchorY = Math.min(window.pageYOffset, anchorY)
    } else {
        anchorY = Math.max(window.pageYOffset - headerHeight, anchorY)
    }

    if (window.innerWidth < 1200) {
        headerNode.style.marginTop = Math.min(0, anchorY - window.pageYOffset) + "px"
    } else {
        headerNode.style.marginTop = "0px"
    }
})

onInteraction(document, function(e) {
    if (pdfLinks.classList.contains("active") && !e.target.closest(".pdf-links")) {
        togglePdfLinks()
    }
})

let activeTarget = null;
let activePopper = null;
let activePopperNode = null;
let popperDestroyTimeout = null;

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

    let footnoteNum = e.target.innerText
    let footnoteNode = document.querySelector(`.footnote li:nth-child(${footnoteNum})`)
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

// function getFootnoteData(footnote) {
//     console.log("getData ????", footnote);
//     return new Promise((resolve, reject) => {
//         let fnoteNode = document.querySelector(`.footnote li:nth-child(${footnote})`)
//         console.log("???", fnoteNode.id)
//         if (!fnoteNode) {
//             reject(`Invalid footnote: ${footnote}`)
//         } else {
//             resolve({"footnoteId": fnoteNode.id})
//         }
//   })
// }

// function getFootnoteHeading(data) {
//     console.log("havaHeading ????", data);
//     return `<code>${data.footnoteId.slice(3)}</code>`
// }

// function getFootnoteBody(data) {
//     console.log("havaBODY ????", data);
//     let fnoteNode = document.getElementById(data.footnoteId)
//     return fnoteNode.children[0]
// }

// var hovercards = new window.Hovercard({
//   noCache   : true,
//   selector  : ".footnote-ref",
//   getData   : getFootnoteData,
//   getHeading: getFootnoteHeading,
//   getBody   : getFootnoteBody,
// });
// console.log(hovercards)

})();
