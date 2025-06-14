import { IconAlertCircle } from '@tabler/icons-react';
import { VariantProps, tv } from 'tailwind-variants';

import slugify from '../../../utils/slugify';
import ContentWrapper from '../../ContentWrapper/ContentWrapper';
import Icon, { IconProp } from '../../Icon/Icon';
import Typography from '../../Typography/Typography';

const formFieldStyles = tv({
  slots: {
    wrapper: 'flex-1 space-y-2',
    contentWrapper: 'flex flex-1 gap-2',
    labelWrapper: 'flex cursor-pointer items-center justify-between gap-1',
    label: 'inline-flex cursor-pointer',
    requiredIndicator: 'ml-1',
    error: 'flex items-center gap-1'
  },
  variants: {
    colorRole: {
      primary: {
        label: 'text-text-primary'
      },
      muted: {
        label: 'text-text-muted'
      }
    },
    direction: {
      vertical: {
        contentWrapper: 'flex-col'
      },
      horizontal: {
        contentWrapper: 'flex-row items-center'
      }
    },
    isRequired: {
      false: {
        requiredIndicator: 'opacity-0'
      }
    },
    isReversed: {
      true: {
        contentWrapper: 'flex-row-reverse'
      }
    },
    isDisabled: {
      true: {
        label: 'cursor-not-allowed text-text-muted'
      }
    }
  },
  defaultVariants: {
    direction: 'vertical',
    isRequired: false,
    isReversed: false,
    isDisabled: false,
    colorRole: 'primary'
  }
});

export interface FormFieldProps
  extends VariantProps<typeof formFieldStyles>,
    React.HTMLAttributes<HTMLDivElement> {
  label?: string;
  errorMessage?: React.ReactNode;
  hint?: React.ReactNode;
  contentRight?: React.ReactNode;
  isRequired?: boolean;
  icon?: IconProp;
}

const {
  wrapper,
  contentWrapper,
  labelWrapper,
  label: labelStyles,
  requiredIndicator,
  error
} = formFieldStyles();

/** @deprecated Use FormField instead */
const FormField = ({
  label,
  errorMessage,
  hint,
  contentRight,
  direction,
  isDisabled = false,
  isRequired = false,
  isReversed = false,
  icon,
  id: _id,
  className,
  colorRole,
  children,
  ...props
}: FormFieldProps) => {
  if (!label && !_id) {
    throw new Error('Either label or id is required');
  }

  const id = _id || slugify(label as string);

  return (
    <div className={wrapper({ className, isDisabled })} {...props}>
      <div className={contentWrapper({ direction, isReversed })}>
        {label || contentRight ? (
          <div className={labelWrapper()}>
            {label && (
              <Typography asChild variant="labelSm">
                <label
                  htmlFor={id}
                  className={labelStyles({ isDisabled, colorRole })}
                >
                  <ContentWrapper
                    align="start"
                    iconLeft={icon}
                    contentRight={
                      isRequired && (
                        <Typography
                          colorRole="danger"
                          variant="labelSm"
                          asChild
                        >
                          <span className={requiredIndicator({ isRequired })}>
                            *
                          </span>
                        </Typography>
                      )
                    }
                  >
                    {label}
                  </ContentWrapper>
                </label>
              </Typography>
            )}
            {contentRight}
          </div>
        ) : null}
        {children}
      </div>
      {hint && (
        <Typography variant="bodySm" colorRole="muted">
          {hint}
        </Typography>
      )}
      {errorMessage && (
        <Typography variant="bodySm" colorRole="danger" className={error()}>
          <Icon icon={IconAlertCircle} className="-translate-y-px" />
          {errorMessage}
        </Typography>
      )}
    </div>
  );
};

FormField.displayName = 'FormField';

export default FormField;
