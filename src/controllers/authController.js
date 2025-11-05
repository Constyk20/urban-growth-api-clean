const User = require('../models/user');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

const signToken = (id) => jwt.sign({ id }, process.env.JWT_SECRET, { expiresIn: '7d' });

exports.register = async (req, res) => {
  const { email, password } = req.body;
  try {
    if (await User.findOne({ email })) return res.status(400).json({ message: 'User exists' });
    const user = await User.create({ email, password });
    res.status(201).json({ _id: user._id, email, token: signToken(user._id) });
  } catch (e) { res.status(500).json({ message: e.message }); }
};

exports.login = async (req, res) => {
  const { email, password } = req.body;
  try {
    const user = await User.findOne({ email });
    if (!user || !(await bcrypt.compare(password, user.password)))
      return res.status(400).json({ message: 'Invalid credentials' });
    res.json({ _id: user._id, email, token: signToken(user._id) });
  } catch (e) { res.status(500).json({ message: e.message }); }
};