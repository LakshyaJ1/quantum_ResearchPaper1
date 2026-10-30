// Render the deck's icon set (Font Awesome via react-icons) to 256 px PNGs in several colours.
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');
const fa = require('react-icons/fa');

const names = ['FaKey', 'FaLock', 'FaLockOpen', 'FaEye', 'FaEyeSlash', 'FaBroadcastTower', 'FaRoute',
  'FaSlidersH', 'FaBatteryQuarter', 'FaUserSecret', 'FaCheck', 'FaTimes', 'FaProjectDiagram',
  'FaBolt', 'FaCut', 'FaHourglassHalf', 'FaDatabase', 'FaRobot', 'FaFlask', 'FaLightbulb',
  'FaEnvelope', 'FaGithub', 'FaShieldAlt', 'FaClock', 'FaDice', 'FaBalanceScale', 'FaClipboardCheck',
  'FaChartBar', 'FaExclamationTriangle', 'FaQuestion', 'FaCogs', 'FaLayerGroup', 'FaSatelliteDish',
  'FaMicroscope', 'FaWarehouse', 'FaBullhorn', 'FaPlus', 'FaEquals', 'FaArrowRight'];
const colours = { white: '#FFFFFF', navy: '#002060', teal: '#1F6E8C', red: '#C00000', grey: '#8A93A6' };
const out = path.join(__dirname, 'png');
fs.mkdirSync(out, { recursive: true });

(async () => {
  for (const n of names) {
    for (const [cname, hex] of Object.entries(colours)) {
      const svg = renderToStaticMarkup(React.createElement(fa[n], { size: 256, color: hex }));
      await sharp(Buffer.from(svg)).resize(256, 256, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
        .png().toFile(path.join(out, `${n}_${cname}.png`));
    }
  }
  console.log('icons:', fs.readdirSync(out).length);
})();
