import FormFieldContent from '@/app/_ui/components/FormField/FormFieldContent';
import FormFieldLabel from '@/app/_ui/components/FormField/FormFieldLabel';
import FormFieldLabelContent from '@/app/_ui/components/FormField/FormFieldLabelContent';

import Typography from '../Typography/Typography';

/**
 * @deprecated This component is only for temporary use until we have a good way
 *   to show listings.
 */
const ReadOnlyField = ({ label, value }: { label: string; value: string }) => {
  return (
    <>
      <FormFieldContent direction="horizontal" className="items-start">
        <FormFieldLabel
          colorRole="muted"
          className="mt-1.5 min-w-28 max-w-28 truncate"
        >
          <FormFieldLabelContent>{label}</FormFieldLabelContent>
        </FormFieldLabel>
        <Typography variant="bodySm" className="grow p-0.5 pl-2 pt-1" asChild>
          <span
            className="block cursor-pointer truncate"
            onClick={(e) => {
              const target = e.currentTarget;
              if (target.scrollWidth > target.clientWidth) {
                target.style.whiteSpace =
                  target.style.whiteSpace === 'normal' ? 'nowrap' : 'normal';
                target.style.textOverflow =
                  target.style.whiteSpace === 'normal' ? 'clip' : 'ellipsis';
              }
            }}
            style={{
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
          >
            {value}
          </span>
        </Typography>
      </FormFieldContent>
    </>
  );
};

export default ReadOnlyField;
