export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <span>© {new Date().getFullYear()} Marginal — three-tier blog application</span>
        <span>React · Express · MySQL</span>
      </div>
    </footer>
  );
}
