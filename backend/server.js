const express = require("express");
const cors = require("cors");

const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
    res.send("FuelAssist Backend Running");
});

app.post("/register", (req, res) => {
    const userData = req.body;

    console.log("User Registered:", userData);

    res.json({
        success: true,
        message: "Registration successful",
        user: userData
    });
});

const PORT = 5000;

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});