export interface ProseProps extends React.HTMLAttributes<HTMLDivElement> {}

const Prose = ({ children, ...props }: ProseProps) => {
  return (
    <div className="prose" {...props}>
      {children}
    </div>
  );
};

export default Prose;
