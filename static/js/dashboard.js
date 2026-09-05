document.addEventListener("DOMContentLoaded", () => {
  const drawer = document.getElementById("tool-drawer");
  if (!drawer) return;

  const drawerTitle = document.getElementById("drawer-title");
  const drawerDescription = document.getElementById("drawer-description");
  const drawerAction = document.getElementById("drawer-action");
  const drawerIcon = document.getElementById("drawer-icon");
  const closeButtons = document.querySelectorAll("[data-close-drawer]");
  const cards = document.querySelectorAll(".workspace-card");

  let activeCard = null;

  function openDrawer(card) {
    activeCard = card;
    const tool = card.dataset.tool || "";
    const description = card.dataset.description || "";
    const action = card.dataset.action || "Continue";
    const href = card.dataset.href || "#";
    const iconSpan = card.querySelector(".card-icon");
    const iconText = iconSpan ? iconSpan.textContent.trim() : "?";

    if (drawerTitle) drawerTitle.textContent = tool;
    if (drawerDescription) drawerDescription.textContent = description;
    if (drawerAction) {
      drawerAction.textContent = action;
      drawerAction.setAttribute("href", href);
    }
    if (drawerIcon) drawerIcon.textContent = iconText;

    drawer.classList.add("open");
    drawer.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";

    const panel = drawer.querySelector(".drawer-panel");
    if (panel) {
      panel.focus();
    }
  }

  function closeDrawer() {
    drawer.classList.remove("open");
    drawer.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    if (activeCard) {
      activeCard.focus();
      activeCard = null;
    }
  }

  cards.forEach((card) => {
    card.addEventListener("click", () => openDrawer(card));
  });

  closeButtons.forEach((btn) => {
    btn.addEventListener("click", closeDrawer);
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && drawer.classList.contains("open")) {
      closeDrawer();
    }
  });

  // Touch swipe down to close support
  let touchStartY = 0;
  const panel = drawer.querySelector(".drawer-panel");
  if (panel) {
    panel.addEventListener("touchstart", (e) => {
      touchStartY = e.touches[0].clientY;
    }, { passive: true });

    panel.addEventListener("touchmove", (e) => {
      const touchY = e.touches[0].clientY;
      const diff = touchY - touchStartY;
      if (diff > 80 && panel.scrollTop <= 0) {
        closeDrawer();
      }
    }, { passive: true });
  }
});
