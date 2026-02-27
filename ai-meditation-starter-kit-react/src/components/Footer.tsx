const Footer = () => {
  return (
    <footer className="bg-gray-50 border-t border-gray-200">
      <div className="flex flex-col sm:flex-row justify-between items-center">
        <p className="text-sm text-gray-500">
          © 2025 AI Meditation Starter Kit. All rights reserved.
        </p>
        <div className="flex space-x-6 mt-4 sm:mt-0">
          <a
            href="/privacy-policy"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-500"
          >
            Privacy Policy
          </a>
          <a
            href="/terms-of-service"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-500"
          >
            Terms of Service
          </a>
        </div>
      </div>
    </footer>
  );
};
export default Footer;
