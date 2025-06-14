import ContentWrapper, {
  ContentWrapperProps
} from '../ContentWrapper/ContentWrapper';
import Typography from '../Typography/Typography';

export interface FormFieldLabelContentProps extends ContentWrapperProps {
  isRequired?: boolean;
}

const FormFieldLabelContent = ({
  contentRight,
  isRequired,
  children,
  size = 'sm',
  align = 'start',
  ...props
}: React.PropsWithChildren<FormFieldLabelContentProps>) => {
  if (contentRight && isRequired) {
    throw new Error(
      'FormFieldLabelContent: contentRight and isRequired cannot be used together'
    );
  }

  return (
    <ContentWrapper
      contentRight={
        contentRight ||
        (isRequired && (
          <Typography colorRole="danger" variant="labelSm" asChild>
            <span>*</span>
          </Typography>
        ))
      }
      size={size}
      align={align}
      {...props}
    >
      {children}
    </ContentWrapper>
  );
};

export default FormFieldLabelContent;
