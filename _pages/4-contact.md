---
permalink: /contact/
title: "Contact us"
---

Fill out the form below to send us a message about a CNV request or a mistake in the data.

<form
  action="https://formspree.io/f/xkgovkzr"
  method="POST"
  enctype="multipart/form-data"
>
  <label for="name">
    Your name:
    <input type="text" name="name" id="name" required>
  </label>

  <label for="email">
    Your email:
    <input type="email" name="email" id="email" required>
  </label>

  <label for="message">
    Your message:
    <textarea name="message" id="message" required></textarea>
  </label>

  <button type="submit">Send</button>
</form>