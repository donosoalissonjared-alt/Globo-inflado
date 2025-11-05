// server.js
const express = require("express");
const app = express();
app.use(express.static("public"));
app.use(express.json());

let story = {
  start: {
    text: "You arrive at the mouth of the Goblin’s Cave. A torch flickers inside.",
    choices: [
      { text: "Enter the cave", next: "cave" },
      { text: "Return to the village", next: "village" }
    ]
  },
  cave: {
    text: "Inside, you hear growls. A goblin leaps at you!",
    choices: [
      { text: "Fight", next: "fight" },
      { text: "Run away", next: "escape" }
    ]
  },
  fight: {
    text: "You swing your sword! Roll a d20 to attack.",
    roll: true,
    nextOnSuccess: "victory",
    nextOnFail: "defeat"
  },
  victory: {
    text: "Critical hit! The goblin falls. You grab the crystal and return a hero.",
    choices: [{ text: "Play again", next: "start" }]
  },
  defeat: {
    text: "Your strike misses. The goblin knocks you out. You wake up outside the cave.",
    choices: [{ text: "Try again", next: "start" }]
  },
  escape: {
    text: "You flee safely but the village remains cursed. Maybe another day…",
    choices: [{ text: "Restart", next: "start" }]
  },
  village: {
    text: "You return to the village empty-handed. They look disappointed.",
    choices: [{ text: "Go back to cave", next: "start" }]
  }
};

app.get("/story/:id", (req, res) => {
  const node = story[req.params.id];
  res.json(node || story.start);
});

app.post("/roll", (req, res) => {
  const roll = Math.floor(Math.random() * 20) + 1;
  const success = roll >= 10;
  res.json({ roll, success });
});

app.listen(3000, () => console.log("Running on port 3000"));
