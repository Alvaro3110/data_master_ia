import "@testing-library/jest-dom";

jest.mock("react-markdown", () => {
  return function MockReactMarkdown({ children }: any) {
    return children;
  };
});

jest.mock("remark-gfm", () => jest.fn());
