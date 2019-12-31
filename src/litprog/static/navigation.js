(function() {
  var cl = document.body.classList
  function toggle_color_theme(e) {
    var content = document.querySelector(".content");
    content.style.visibility = "hidden";
    if (cl.contains("dark")) {
      cl.remove("dark");
      cl.add("light");
    } else {
      cl.remove("light");
      cl.add("dark");
    }
    cl.add("animate");
    setTimeout(function(){
      content.style.visibility = "visible";
    }, 800);
    var prev_theme = localStorage.getItem("litprog_theme")
    if (prev_theme == "dark") {
        localStorage.setItem("litprog_theme", "light");
    } else {
        localStorage.setItem("litprog_theme", "dark");
    }
    e.stopPropagation();
  }

  function toggle_typeface(e) {
    if (cl.contains("font-slab")) {
      cl.remove("font-slab");
      cl.add("font-serif");
      localStorage.setItem("litprog_font", "serif");
    } else if (cl.contains("font-serif")) {
      cl.remove("font-serif");
      cl.add("font-sans");
      localStorage.setItem("litprog_font", "sans");
    } else {
      cl.remove("font-sans");
      cl.add("font-slab");
      localStorage.setItem("litprog_font", "slab");
    }
    e && e.stopPropagation();
  }

  document.getElementById("toggle-theme").addEventListener("click", toggle_color_theme);
  document.getElementById("toggle-font").addEventListener("click", toggle_typeface);
  document.getElementById("toggle-print").addEventListener("click", function(e) {
    document.getElementById("pdf").classList.toggle("active")
    e.stopPropagation();
  });
  document.getElementById("pdf").addEventListener("click", function(e) {
    e.stopPropagation();
  });
  document.addEventListener('click', function(e) {
    document.getElementById("pdf").classList.remove("active")
  });

  document.addEventListener('keydown', function(e) {
    if (e.key == "Alt") {return;}
    if (!e.altKey) {return;}

    // var styles = window.getComputedStyle(document.body, "p")
    // var line_height_str = styles.getPropertyValue("line-height");
    // var line_height_px = parseInt(line_height_str.slice(0, -2));
    //
    // var extra_scroll = 0;
    //
    // if (e.key == "j") {extra_scroll = line_height_px * 3;}
    // if (e.key == "J") {extra_scroll = line_height_px * 9;}
    // if (e.key == "k") {extra_scroll = line_height_px * -3;}
    // if (e.key == "K") {extra_scroll = line_height_px * -9;}
    //
    // if (extra_scroll !== 0) {
    //     window.scrollBy(0, extra_scroll);
    // }

    if (e.key == "j") {
        // Next Headline
    }
    if (e.key == "k") {
        // Previous Headline
    }
    if (e.key == "l") {
        // Next Chapter
    }
    if (e.key == "h") {
        // Previous Chapter
    }
    if (e.key == "t") {
        toggle_typeface(e);
    }
    if (e.key == "c") {
        toggle_color_theme(e);
    }
  });
})();