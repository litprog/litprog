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
    let headingsOffset = 0
    for (var i = 0; i < headingNodes.length; i++) {
        let headingNode = headingNodes[i]
        let headingOffset = headingNode.offsetTop + wrapperOffset
        if (headingOffset > window.pageYOffset) {
            let newActiveNav = navigationNodes[i + headingsOffset]
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

})();
